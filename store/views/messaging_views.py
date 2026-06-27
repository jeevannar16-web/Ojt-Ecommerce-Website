"""Messaging system — buyer-seller chat, seller-admin support tickets, conversation lists, and unread polling."""

import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from store.models import Conversation, Message, Product, BlockedUser, UserOnline, MessageReport
from store.activity_logger import log_action
from django.contrib.auth.models import User
from users.models import Profile
from django.views.decorators.http import require_POST


# ==============================================================================
# SECTION: Conversation List
# ==============================================================================

@login_required
def conversation_list(request):
    user = request.user
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if user.is_staff:
        conversations = Conversation.objects.all().select_related('customer', 'seller', 'product').prefetch_related('messages')
    else:
        conversations = Conversation.objects.filter(
            Q(customer=user) | Q(seller=user)
        ).select_related('customer', 'seller', 'product').prefetch_related('messages')

    ctx = []
    seller_ids = set()
    product_ids = set()

    for c in conversations:
        last = c.last_message()

        # Determine the other user safely
        if user.is_staff:
            other = c.customer
        elif c.customer == user:
            other = c.seller
        else:
            other = c.customer

        # Skip orphaned conversations where other party is missing
        if other is None:
            continue

        if c.seller and c.seller.id != user.id:
            seller_ids.add(c.seller.id)
        if c.product:
            product_ids.add(c.product.id)

        other_status_emoji = ''
        other_status_text = ''
        store_slug = ''
        try:
            p = Profile.objects.get(user=other)
            other_status_emoji = p.status_emoji or ''
            other_status_text = p.status_text or ''
            store_slug = p.store_slug or ''
        except Profile.DoesNotExist:
            pass

        ctx.append({
            'conv': c,
            'last_message': last,
            'unread': c.unread_count(user),
            'other_user': other,
            'other_status_emoji': other_status_emoji,
            'other_status_text': other_status_text,
            'store_slug': store_slug,
            'product': c.product,
        })

    is_seller = hasattr(user, 'profile') and user.profile.is_seller
    base_ctx = {
        'conversations': ctx,
        'unread_total': sum(c['unread'] for c in ctx),
        'is_admin': user.is_staff,
        'is_seller': is_seller,
        'now': now,
        'today': today_start,
        'yesterday': now - timedelta(days=1),
        'week_ago': now - timedelta(days=7),
    }

    if user.is_staff:
        total_conv = conversations.count()
        unread_total = sum(c.unread_count(user) for c in conversations)
        active_today = conversations.filter(updated_at__gte=today_start).count()
        support_count = conversations.filter(is_admin_conversation=True).count()
        product_inquiry_count = conversations.filter(
            is_admin_conversation=False, product__isnull=False
        ).exclude(is_admin_conversation=True).count()
        overdue = conversations.filter(
            updated_at__lt=now - timedelta(hours=48),
            messages__isnull=False
        ).distinct().count()

        base_ctx['stats'] = {
            'total': total_conv,
            'unread': unread_total,
            'active_today': active_today,
            'support': support_count,
            'product_inquiries': product_inquiry_count,
            'overdue': overdue,
        }
        return render(request, 'store/messages/admin_list.html', base_ctx)

    base_ctx['seller_count'] = len(seller_ids)
    base_ctx['product_count'] = len(product_ids)

    # Customers get a dedicated professional page
    if not is_seller:
        # Fetch profile info for each other user
        for item in ctx:
            try:
                p = Profile.objects.get(user=item['other_user'])
                item['store_name'] = p.store_name or ''
                item['other_user_profile'] = p
            except Profile.DoesNotExist:
                item['store_name'] = ''
                item['other_user_profile'] = None
        return render(request, 'store/messages/customer_list.html', base_ctx)

    return render(request, 'store/messages/list.html', base_ctx)


# ==============================================================================
# SECTION: Conversation Detail
# ==============================================================================

@login_required
def conversation_detail(request, conversation_id):
    conv = get_object_or_404(Conversation, id=conversation_id)
    user = request.user
    if user != conv.customer and user != conv.seller and not user.is_staff:
        django_messages.error(request, "You don't have access to this conversation.")
        return redirect('store:messages_list')

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            msg = Message.objects.create(conversation=conv, sender=user, content=content)
            conv.updated_at = timezone.now()
            conv.save(update_fields=['updated_at'])
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'id': msg.id,
                    'content': msg.content,
                    'created_at': msg.created_at.strftime('%H:%M'),
                    'sender': msg.sender.username,
                    'is_mine': True,
                })
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'empty'}, status=400)
        return redirect('store:conversation_detail', conversation_id=conv.id)

    # Mark as delivered and read
    conv.messages.filter(is_read=False).exclude(sender=user).update(is_delivered=True, is_read=True)

    if user.is_staff:
        other_user = conv.customer if user == conv.seller else conv.seller
    else:
        other_user = conv.seller if conv.customer == user else conv.customer

    # Safely handle missing other_user
    if other_user is None:
        django_messages.error(request, "This conversation is missing a participant.")
        return redirect('store:messages_list')

    other_user_profile = None
    try:
        other_user_profile = Profile.objects.get(user=other_user)
    except Profile.DoesNotExist:
        pass

    seller_profile = None
    seller_product_count = 0
    if not user.is_staff and not conv.is_admin_conversation:
        seller = conv.seller
        if seller:
            try:
                seller_profile = Profile.objects.get(user=seller)
                seller_product_count = Product.objects.filter(seller=seller).count()
            except Profile.DoesNotExist:
                pass

    now = timezone.now()
    yesterday = now - timedelta(days=1)

    is_blocked = BlockedUser.objects.filter(blocker=user, blocked=other_user).exists()
    pinned_message = conv.messages.filter(is_pinned=True).first()

    is_seller = hasattr(user, 'profile') and user.profile.is_seller

    status_options = [
        ('🟢', 'Available'), ('🟠', 'Busy'), ('🔴', 'DND'),
        ('🌙', 'Away'), ('💼', 'At Work'), ('📞', 'On Call'),
        ('🏠', 'At Home'), ('⚡', 'Online'),
    ]

    context = {
        'conversation': conv,
        'messages': conv.messages.select_related('sender'),
        'other_user': other_user,
        'is_admin': user.is_staff,
        'seller_profile': seller_profile,
        'seller_product_count': seller_product_count,
        'now': now,
        'yesterday': yesterday,
        'theme_choices': Conversation.THEME_CHOICES,
        'is_blocked': is_blocked,
        'pinned_message': pinned_message,
        'other_user_profile': other_user_profile,
        'status_options': status_options,
    }

    # Customers get a dedicated professional chat page
    if not user.is_staff and not is_seller:
        return render(request, 'store/messages/customer_detail.html', context)

    return render(request, 'store/messages/detail.html', context)


# ==============================================================================
# SECTION: Start Conversation
# ==============================================================================

@login_required
def start_conversation(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    seller = product.seller
    if not seller:
        django_messages.error(request, "This product has no seller assigned.")
        return redirect('store:product_detail', product_id=product.id)

    if request.user == seller:
        django_messages.info(request, "You can't chat with yourself about your own product.")
        return redirect('store:product_detail', product_id=product.id)

    conv = Conversation.objects.filter(
        customer=request.user, seller=seller, product=product
    ).first()

    if not conv:
        conv = Conversation.objects.create(
            customer=request.user,
            seller=seller,
            product=product,
            subject=f"Inquiry about {product.name}",
        )
        log_action(request.user, 'conversation_start',
                   f"Started conversation about {product.name} with {seller.username}",
                   {'product_id': product.id, 'seller_id': seller.id}, request)

    return redirect('store:conversation_detail', conversation_id=conv.id)


# ==============================================================================
# SECTION: Contact Admin
# ==============================================================================

@login_required
def contact_admin(request):
    user = request.user
    is_seller = hasattr(user, 'profile') and user.profile.is_seller or user.is_staff
    if not is_seller:
        django_messages.error(request, "Only sellers can contact admin support.")
        return redirect('store:messages_list')

    admins = User.objects.filter(is_staff=True)
    if not admins.exists():
        django_messages.error(request, "No admin available. Please try again later.")
        return redirect('store:seller_dashboard' if is_seller else 'home')

    admin = admins.first()
    conv = Conversation.objects.filter(
        customer=user, seller=admin, is_admin_conversation=True
    ).first()

    if not conv:
        conv = Conversation.objects.create(
            customer=user,
            seller=admin,
            subject="Seller Support Inquiry",
            is_admin_conversation=True,
        )
        log_action(user, 'admin_contact',
                   f"{user.username} contacted admin support",
                   {'admin_id': admin.id}, request)

    return redirect('store:conversation_detail', conversation_id=conv.id)


# ==============================================================================
# SECTION: API - Edit Message
# ==============================================================================

@login_required
def api_edit_message(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    data = json.loads(request.body)
    msg_id = data.get('message_id')
    new_content = data.get('content', '').strip()
    if not msg_id or not new_content:
        return JsonResponse({'error': 'message_id and content required'}, status=400)
    msg = get_object_or_404(Message, id=msg_id, sender=request.user)
    delta = timezone.now() - msg.created_at
    if delta.total_seconds() > 300:
        return JsonResponse({'error': 'Can only edit within 5 minutes'}, status=403)
    msg.content = new_content
    msg.edited = True
    msg.save(update_fields=['content', 'edited'])
    return JsonResponse({'ok': True, 'content': new_content})


# ==============================================================================
# SECTION: API - Unread Count
# ==============================================================================

@login_required
def api_unread_count(request):
    user = request.user
    if user.is_staff:
        conversations = Conversation.objects.all()
    else:
        conversations = Conversation.objects.filter(
            Q(customer=user) | Q(seller=user)
        )
    total = sum(c.unread_count(user) for c in conversations)
    return JsonResponse({'unread': total})


# ==============================================================================
# SECTION: API - New Messages
# ==============================================================================

@login_required
def api_new_messages(request, conversation_id):
    conv = get_object_or_404(Conversation, id=conversation_id)
    user = request.user
    if user != conv.customer and user != conv.seller and not user.is_staff:
        return JsonResponse({'error': 'forbidden'}, status=403)

    since = request.GET.get('since', '0')
    try:
        since_id = int(since)
    except (ValueError, TypeError):
        since_id = 0

    new_msgs = conv.messages.filter(id__gt=since_id).select_related('sender')
    data = []
    for m in new_msgs:
        file_url = m.file.url if m.file else None
        file_name = None
        file_size = None
        file_mime_type = None
        if m.file:
            file_name = m.file.name.split('/')[-1]
            try:
                file_size = m.file.size
            except (OSError, NotImplementedError):
                file_size = None
            file_mime_type = m.mime_type
        data.append({
            'id': m.id,
            'sender': m.sender.username,
            'content': m.content,
            'image': m.image.url if m.image else None,
            'file_url': file_url,
            'file_type': m.file_type or None,
            'file_name': file_name,
            'file_size': file_size,
            'file_mime_type': file_mime_type,
            'reactions': m.reactions,
            'created_at': m.created_at.strftime('%H:%M'),
            'is_mine': m.sender == user,
            'edited': m.edited,
            'is_pinned': m.is_pinned,
            'is_read': m.is_read,
            'is_delivered': m.is_delivered,
            'is_deleted': m.is_deleted,
            'read_at': None,
        })
    return JsonResponse({'messages': data, 'now': timezone.now().timestamp(), 'theme': conv.theme})


# ==============================================================================
# SECTION: API - React to Message
# ==============================================================================

@login_required
@require_POST
def api_react_message(request):
    data = json.loads(request.body)
    msg_id = data.get('message_id')
    emoji = data.get('emoji', '').strip()
    if not msg_id or not emoji:
        return JsonResponse({'error': 'message_id and emoji required'}, status=400)
    msg = get_object_or_404(Message, id=msg_id)
    conv = msg.conversation
    user = request.user
    if user != conv.customer and user != conv.seller and not user.is_staff:
        return JsonResponse({'error': 'forbidden'}, status=403)
    reactions = msg.reactions or {}
    users_for_emoji = reactions.get(emoji, [])
    username = user.username
    if username in users_for_emoji:
        users_for_emoji.remove(username)
        if not users_for_emoji:
            reactions.pop(emoji, None)
        else:
            reactions[emoji] = users_for_emoji
    else:
        users_for_emoji.append(username)
        reactions[emoji] = users_for_emoji
    msg.reactions = reactions
    msg.save(update_fields=['reactions'])
    return JsonResponse({'ok': True, 'reactions': reactions})


@login_required
def api_heartbeat(request):
    status, _ = UserOnline.objects.get_or_create(user=request.user)
    status.is_online = True
    status.last_seen = timezone.now()
    status.save(update_fields=['is_online', 'last_seen'])
    return JsonResponse({'ok': True})


@login_required
def api_reaction_updates(request, conversation_id):
    conv = get_object_or_404(Conversation, id=conversation_id)
    user = request.user
    if user != conv.customer and user != conv.seller and not user.is_staff:
        return JsonResponse({'error': 'forbidden'}, status=403)
    ids = request.GET.get('ids', '')
    if not ids:
        return JsonResponse({'reactions': {}})
    try:
        msg_ids = [int(x) for x in ids.split(',') if x.strip().isdigit()]
    except (ValueError, TypeError):
        return JsonResponse({'reactions': {}})
    msgs = Message.objects.filter(id__in=msg_ids, conversation=conv).only('id', 'reactions')
    result = {}
    for m in msgs:
        if m.reactions:
            result[str(m.id)] = m.reactions
    pinned = conv.messages.filter(is_pinned=True).only('id', 'content').first()
    return JsonResponse({
        'reactions': result,
        'pinned_id': pinned.id if pinned else None,
        'pinned_content': pinned.content[:80] if pinned else None,
    })


# ==============================================================================
# SECTION: API - Upload Image
# ==============================================================================

@login_required
@require_POST
def api_upload_image(request):
    conv_id = request.POST.get('conversation_id')
    if not conv_id:
        return JsonResponse({'error': 'conversation_id required'}, status=400)
    conv = get_object_or_404(Conversation, id=conv_id)
    user = request.user
    if user != conv.customer and user != conv.seller and not user.is_staff:
        return JsonResponse({'error': 'forbidden'}, status=403)
    if 'image' not in request.FILES:
        return JsonResponse({'error': 'No image uploaded'}, status=400)
    image = request.FILES['image']
    if image.size > 5 * 1024 * 1024:
        return JsonResponse({'error': 'Image must be under 5MB'}, status=400)
    msg = Message.objects.create(
        conversation=conv, sender=user,
        content=request.POST.get('content', '').strip(),
        image=image,
    )
    conv.updated_at = timezone.now()
    conv.save(update_fields=['updated_at'])
    return JsonResponse({
        'ok': True,
        'message_id': msg.id,
        'image_url': msg.image.url,
        'created_at': msg.created_at.strftime('%H:%M'),
    })


# ==============================================================================
# SECTION: API - Pin Message
# ==============================================================================

@login_required
@require_POST
def api_pin_message(request):
    data = json.loads(request.body)
    msg_id = data.get('message_id')
    msg = get_object_or_404(Message, id=msg_id)
    conv = msg.conversation
    user = request.user
    if user != conv.customer and user != conv.seller and not user.is_staff:
        return JsonResponse({'error': 'forbidden'}, status=403)
    msg.is_pinned = not msg.is_pinned
    msg.save(update_fields=['is_pinned'])
    return JsonResponse({'ok': True, 'is_pinned': msg.is_pinned})


# ==============================================================================
# SECTION: API - Search Messages
# ==============================================================================

@login_required
def api_search_messages(request, conversation_id):
    conv = get_object_or_404(Conversation, id=conversation_id)
    user = request.user
    if user != conv.customer and user != conv.seller and not user.is_staff:
        return JsonResponse({'error': 'forbidden'}, status=403)
    q = request.GET.get('q', '').strip()
    if not q or len(q) < 2:
        return JsonResponse({'results': []})
    results = conv.messages.filter(content__icontains=q).select_related('sender')[:20]
    data = []
    for m in results:
        data.append({
            'id': m.id,
            'sender': m.sender.username,
            'content': m.content[:120],
            'created_at': m.created_at.strftime('%b %d, %H:%M'),
        })
    return JsonResponse({'results': data})


# ==============================================================================
# SECTION: Block User
# ==============================================================================

@login_required
def block_user(request, conversation_id):
    conv = get_object_or_404(Conversation, id=conversation_id)
    user = request.user
    if user != conv.customer and user != conv.seller:
        django_messages.error(request, "Access denied.")
        return redirect('store:messages_list')
    other = conv.other_user(user)
    if request.method == 'POST':
        existing = BlockedUser.objects.filter(blocker=user, blocked=other).first()
        action = request.POST.get('action', 'block')
        if action == 'block' and not existing:
            BlockedUser.objects.create(
                blocker=user, blocked=other,
                conversation=conv,
                reason=request.POST.get('reason', ''),
            )
            django_messages.success(request, f"Blocked {other.username}")
            log_action(user, 'block_user',
                       f"{user.username} blocked {other.username}",
                       {'conversation_id': conv.id}, request)
        elif action == 'unblock' and existing:
            existing.delete()
            django_messages.success(request, f"Unblocked {other.username}")
        return redirect('store:conversation_detail', conversation_id=conv.id)
    return redirect('store:conversation_detail', conversation_id=conv.id)


# ==============================================================================
# SECTION: API - Mute Conversation
# ==============================================================================

@login_required
@require_POST
def api_mute_conversation(request):
    data = json.loads(request.body)
    conv_id = data.get('conversation_id')
    conv = get_object_or_404(Conversation, id=conv_id)
    user = request.user
    if user != conv.customer and user != conv.seller:
        return JsonResponse({'error': 'forbidden'}, status=403)
    conv.is_muted = not conv.is_muted
    conv.save(update_fields=['is_muted'])
    return JsonResponse({'ok': True, 'is_muted': conv.is_muted})


# ==============================================================================
# SECTION: API - Change Theme
# ==============================================================================

@login_required
@require_POST
def api_change_theme(request):
    data = json.loads(request.body)
    conv_id = data.get('conversation_id')
    theme = data.get('theme', 'dark')
    valid_themes = [t[0] for t in Conversation.THEME_CHOICES]
    if theme not in valid_themes:
        return JsonResponse({'error': 'Invalid theme'}, status=400)
    conv = get_object_or_404(Conversation, id=conv_id)
    user = request.user
    if user != conv.customer and user != conv.seller:
        return JsonResponse({'error': 'forbidden'}, status=403)
    conv.theme = theme
    conv.save(update_fields=['theme'])
    return JsonResponse({'ok': True, 'theme': theme})


# ==============================================================================
# SECTION: API - Upload File
# ==============================================================================

@login_required
@require_POST
def api_upload_file(request):
    conv_id = request.POST.get('conversation_id')
    if not conv_id:
        return JsonResponse({'error': 'conversation_id required'}, status=400)
    conv = get_object_or_404(Conversation, id=conv_id)
    user = request.user
    if user != conv.customer and user != conv.seller and not user.is_staff:
        return JsonResponse({'error': 'forbidden'}, status=403)
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file uploaded'}, status=400)
    uploaded = request.FILES['file']
    if uploaded.size > 20 * 1024 * 1024:
        return JsonResponse({'error': 'File must be under 20MB'}, status=400)

    mime = uploaded.content_type or ''
    if mime.startswith('image/'):
        ftype = 'image'
    elif mime.startswith('video/'):
        ftype = 'video'
    elif mime.startswith('audio/'):
        ftype = 'audio'
    else:
        ftype = 'document'

    msg = Message.objects.create(
        conversation=conv, sender=user,
        content=request.POST.get('content', '').strip(),
        file=uploaded,
        file_type=ftype,
    )
    conv.updated_at = timezone.now()
    conv.save(update_fields=['updated_at'])
    return JsonResponse({
        'ok': True,
        'message_id': msg.id,
        'file_url': msg.file.url,
        'file_type': ftype,
        'file_name': uploaded.name,
        'file_size': uploaded.size,
        'file_mime_type': msg.mime_type,
        'created_at': msg.created_at.strftime('%H:%M'),
    })


# ==============================================================================
# SECTION: API - Delete Message
# ==============================================================================

@login_required
@require_POST
def api_delete_message(request):
    data = json.loads(request.body)
    msg_id = data.get('message_id')
    scope = data.get('scope', 'me')
    msg = get_object_or_404(Message, id=msg_id)
    conv = msg.conversation
    user = request.user
    if user != conv.customer and user != conv.seller and not user.is_staff:
        return JsonResponse({'error': 'forbidden'}, status=403)
    if scope == 'everyone':
        if msg.sender != user and not user.is_staff:
            return JsonResponse({'error': 'Can only delete your own messages for everyone'}, status=403)
    msg.is_deleted = True
    msg.content = ''
    msg.save(update_fields=['is_deleted', 'content'])
    return JsonResponse({'ok': True, 'scope': scope})


# ==============================================================================
# SECTION: API - Report Message
# ==============================================================================

@login_required
@require_POST
def api_report_message(request):
    data = json.loads(request.body)
    msg_id = data.get('message_id')
    reason = data.get('reason', '')
    detail = data.get('detail', '')
    if not msg_id or not reason:
        return JsonResponse({'error': 'message_id and reason required'}, status=400)
    msg = get_object_or_404(Message, id=msg_id)
    valid_reasons = [r[0] for r in MessageReport.REASON_CHOICES]
    if reason not in valid_reasons:
        return JsonResponse({'error': 'Invalid reason'}, status=400)
    MessageReport.objects.create(
        message=msg,
        reported_by=request.user,
        reason=reason,
        detail=detail,
    )
    log_action(request.user, 'report_message',
               f"{request.user.username} reported message #{msg_id} ({reason})",
               {'message_id': msg_id, 'reason': reason}, request)
    return JsonResponse({'ok': True})


# ==============================================================================
# SECTION: API - Online Status
# ==============================================================================

@login_required
@require_POST
def api_online_status(request):
    data = json.loads(request.body)
    user_id = data.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'user_id required'}, status=400)
    target = get_object_or_404(User, id=user_id)
    try:
        status = UserOnline.objects.get(user=target)
        is_online = status.is_online
        last_seen = status.last_seen
    except UserOnline.DoesNotExist:
        is_online = False
        last_seen = None

    now = timezone.now()
    if is_online:
        last_seen_label = 'Online'
        last_seen_ago = ''
    elif last_seen:
        delta = now - last_seen
        if delta < timedelta(minutes=1):
            last_seen_label = 'Just now'
        elif delta < timedelta(hours=1):
            mins = int(delta.total_seconds() // 60)
            last_seen_label = f'{mins}m ago'
        elif delta < timedelta(days=1):
            hours = int(delta.total_seconds() // 3600)
            last_seen_label = f'{hours}h ago'
        else:
            last_seen_label = f'{last_seen.days}d ago'
        last_seen_ago = last_seen_label
    else:
        last_seen_label = 'Offline'
        last_seen_ago = ''

    status_emoji = ''
    status_text = ''
    try:
        profile = Profile.objects.get(user=target)
        status_emoji = profile.status_emoji or ''
        status_text = profile.status_text or ''
    except Profile.DoesNotExist:
        pass

    return JsonResponse({
        'is_online': is_online,
        'is_typing': False,
        'last_seen_label': last_seen_label,
        'last_seen_ago': last_seen_ago,
        'status_emoji': status_emoji,
        'status_text': status_text,
    })


# ==============================================================================
# SECTION: API - User Info
# ==============================================================================

@login_required
@require_POST
def api_user_info(request):
    data = json.loads(request.body)
    user_id = data.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'user_id required'}, status=400)
    target = get_object_or_404(User, id=user_id)

    phone = ''
    city = ''
    store = ''
    status_emoji = ''
    status_text = ''
    try:
        profile = Profile.objects.get(user=target)
        phone = profile.phone or ''
        city = profile.city or ''
        store = profile.store_name or ''
        status_emoji = profile.status_emoji or ''
        status_text = profile.status_text or ''
    except Profile.DoesNotExist:
        pass

    is_online = False
    last_seen_label = 'Offline'
    try:
        status = UserOnline.objects.get(user=target)
        is_online = status.is_online
        if is_online:
            last_seen_label = 'Online'
        elif status.last_seen:
            delta = timezone.now() - status.last_seen
            if delta < timedelta(hours=1):
                mins = int(delta.total_seconds() // 60)
                last_seen_label = f'{mins}m ago'
            elif delta < timedelta(days=1):
                hours = int(delta.total_seconds() // 3600)
                last_seen_label = f'{hours}h ago'
            else:
                last_seen_label = f'{delta.days}d ago'
    except UserOnline.DoesNotExist:
        pass

    return JsonResponse({
        'username': target.username,
        'email': target.email,
        'phone': phone,
        'city': city,
        'store': store,
        'member_since': target.date_joined.strftime('%b %Y'),
        'last_seen': last_seen_label,
        'is_online': is_online,
        'last_seen_label': last_seen_label,
        'status_emoji': status_emoji,
        'status_text': status_text,
    })


# ==============================================================================
# SECTION: API - Start Call
# ==============================================================================

@login_required
@require_POST
def api_start_call(request):
    return JsonResponse({
        'ok': True,
        'message': 'Video call feature coming soon. Use messaging for now.',
        'redirect_url': None,
    })


# ==============================================================================
# SECTION: API - Update Status
# ==============================================================================

@login_required
@require_POST
def api_update_status(request):
    try:
        data = json.loads(request.body)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    emoji = data.get('emoji', '🟢')
    text = data.get('text', 'Available')
    profile = request.user.profile
    profile.status_emoji = emoji
    profile.status_text = text
    profile.save(update_fields=['status_emoji', 'status_text'])
    status, _ = UserOnline.objects.get_or_create(user=request.user)
    status.is_online = True
    status.last_seen = timezone.now()
    status.save(update_fields=['is_online', 'last_seen'])
    return JsonResponse({'ok': True, 'emoji': emoji, 'text': text})


# ==============================================================================
# SECTION: API - Mark Read
# ==============================================================================

@login_required
def api_mark_read(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    conv_id = request.POST.get('conversation_id')
    if not conv_id:
        return JsonResponse({'error': 'conversation_id required'}, status=400)
    conv = get_object_or_404(Conversation, id=conv_id)
    user = request.user
    if user != conv.customer and user != conv.seller and not user.is_staff:
        return JsonResponse({'error': 'forbidden'}, status=403)
    conv.messages.filter(is_read=False).exclude(sender=user).update(is_read=True)
    return JsonResponse({'ok': True})


# ==============================================================================
# SECTION: API - Delete Conversation
# ==============================================================================

@login_required
def api_delete_conversation(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    conv_id = request.POST.get('conversation_id')
    if not conv_id:
        return JsonResponse({'error': 'conversation_id required'}, status=400)
    conv = get_object_or_404(Conversation, id=conv_id)
    user = request.user
    if user != conv.customer and user != conv.seller and not user.is_staff:
        return JsonResponse({'error': 'forbidden'}, status=403)
    conv.delete()
    return JsonResponse({'ok': True})