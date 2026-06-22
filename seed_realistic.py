"""
Comprehensive realistic seed data for the e-commerce platform.
Generates real-looking products, users, orders, favorites, cart items, and reviews.
Run: python seed_realistic.py
"""
import os, sys, random, uuid
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fitness_hub.settings')
import django
django.setup()

from django.contrib.auth.models import User
from django.utils.text import slugify
from store.models import (Category, Product, ProductSize, Order, OrderItem,
                          CartItem, FavoriteItem, Review, ActivityLog)
from users.models import Profile

# ─── Helpers ────────────────────────────────────────────────
def rand_date(days_back=180):
    return datetime.now() - timedelta(days=random.randint(0, days_back),
                                      hours=random.randint(0, 23),
                                      minutes=random.randint(0, 59))

def pick_weighted(options):
    """Pick from list of (weight, item) tuples."""
    total = sum(w for w, _ in options)
    r = random.uniform(0, total)
    upto = 0
    for w, item in options:
        upto += w
        if r <= upto:
            return item
    return options[-1][1]

# ─── Categories (must match existing curated categories) ─────
CATEGORY_IDS = {
    'Dumbbells & Free Weights': 14, 'Barbells & Plates': 5,
    'Kettlebells': 11, 'Resistance Bands & Tubes': 15,
    'Yoga & Pilates': 3, 'Cardio Machines': 1,
    'Home Gym Equipment': 16, 'Fitness Accessories': 8,
    'Gym Gloves & Straps': 4,
    'Shaker Bottles & Blenders': 6, 'Protein Supplements': 6,
    'BCAAs & Aminos': 6, 'Pre-Workout & Energy': 6,
    'Creatine & Mass Gainers': 6, 'Vitamins & Wellness': 6,
    'Fitness Apparel – Men': 12, 'Fitness Apparel – Women': 12,
    'Footwear': 12, 'Gym Bags & Backpacks': 12,
    'Jump Ropes & Speed Ropes': 1,
}
cat_objects = {}

# ─── Products ────────────────────────────────────────────────
PRODUCTS = [
    # Dumbbells & Free Weights
    ('Adjustable Dumbbell Set 20kg', 129.99, 45, 'Dumbbells & Free Weights', 'Professional-grade adjustable dumbbell set with 2x 20kg weight stacks. Smooth dial system for quick weight changes between exercises.'),
    ('Adjustable Dumbbell Set 30kg', 189.99, 30, 'Dumbbells & Free Weights', 'Heavy-duty adjustable dumbbell set reaching 30kg per hand. Perfect for progressive overload training.'),
    ('Cast Iron Dumbbell 5kg Pair', 39.99, 120, 'Dumbbells & Free Weights', 'Durable cast iron dumbbells with firm grip. Ideal for beginners and toning workouts.'),
    ('Cast Iron Dumbbell 10kg Pair', 59.99, 85, 'Dumbbells & Free Weights', 'Medium-weight cast iron dumbbells for intermediate strength training. Knurled handles for secure grip.'),
    ('Cast Iron Dumbbell 15kg Pair', 79.99, 60, 'Dumbbells & Free Weights', 'Heavy cast iron dumbbells for challenging workouts. Rubber coating protects your floor.'),
    ('Hex Dumbbell 8kg Single', 24.99, 200, 'Dumbbells & Free Weights', 'Hexagonal design prevents rolling. Perfect for lunges, rows, and core work. Sold individually.'),
    ('Neoprene Dumbbell Set 2x3kg', 29.99, 150, 'Dumbbells & Free Weights', 'Colorful neoprene-coated dumbbells for cardio and light resistance training.'),
    # Barbells & Plates
    ('Olympic Barbell 20kg – 7ft', 149.99, 25, 'Barbells & Plates', 'Professional 20kg Olympic barbell with dual knurl marks and 210,000 PSI tensile strength.'),
    ('Bumper Plate Set 100kg', 299.99, 15, 'Barbells & Plates', 'Complete 100kg bumper plate set with 10kg–25kg pairs. Dead bounce technology for quiet drops.'),
    ('Rubber Grip Plate 5kg', 24.99, 300, 'Barbells & Plates', 'Easy-grip rubber plate with color coding. Fits all Olympic bars.'),
    ('Rubber Grip Plate 10kg', 39.99, 200, 'Barbells & Plates', 'Durable rubber plate with ergonomic grip holes. Crumb rubber construction.'),
    ('Rubber Grip Plate 20kg', 69.99, 100, 'Barbells & Plates', 'Heavy-duty rubber plate for serious lifting. Color-coded for quick identification.'),
    ('EZ Curl Bar 10kg', 69.99, 40, 'Barbells & Plates', 'EZ curl bar for bicep and tricep exercises. Ergonomic wave grip reduces wrist strain.'),
    ('Hex Bar / Trap Bar 25kg', 159.99, 20, 'Barbells & Plates', 'Hexagonal deadlift bar with high handles and low handles. Perfect for deadlifts and shrugs.'),
    # Kettlebells
    ('Kettlebell 8kg Cast Iron', 29.99, 100, 'Kettlebells', 'Single cast-iron kettlebell with flat base. Excellent for swings, goblet squats, and Turkish get-ups.'),
    ('Kettlebell 12kg Competition', 44.99, 75, 'Kettlebells', 'Competition-grade kettlebell with uniform size across weights. Color-coded weight marking.'),
    ('Kettlebell 16kg Powder Coat', 49.99, 60, 'Kettlebells', 'Powder-coated finish for durable grip. Wide handle for two-hand swings.'),
    ('Kettlebell 24kg Competition', 74.99, 35, 'Kettlebells', 'Professional competition kettlebell. Perfect for advanced swing and snatch work.'),
    ('Kettlebell Set 3-Piece (8/12/16kg)', 109.99, 25, 'Kettlebells', 'Value set with three kettlebells for progressive training. Ideal for home gyms.'),
    # Resistance Bands
    ('Resistance Band Set – 5 Levels', 34.99, 200, 'Resistance Bands & Tubes', 'Set of 5 bands from light to extra-heavy. Latex-free and snap-resistant. Includes carry bag.'),
    ('Loop Resistance Bands 6-Pack', 24.99, 300, 'Resistance Bands & Tubes', 'Glute band set for lower body workouts. Non-slip fabric outer layer.'),
    ('Pull-Up Assist Band Long Loop', 19.99, 150, 'Resistance Bands & Tubes', 'Long loop band for pull-up assistance and stretching. 41" length, multiple resistance levels.'),
    ('Mini Resistance Bands 4-Pack', 14.99, 400, 'Resistance Bands & Tubes', 'Compact mini bands for activation and mobility work. Great for warm-ups and rehab.'),
    ('Tube Resistance Band with Handles', 29.99, 120, 'Resistance Bands & Tubes', 'Dual tube system with foam handles and ankle straps. Multiple resistance tubes included.'),
    # Yoga & Pilates
    ('Premium Yoga Mat 6mm', 49.99, 90, 'Yoga & Pilates', 'Eco-friendly TPE yoga mat with alignment lines. Non-slip on both sides. Includes carry strap.'),
    ('Extra Thick Yoga Mat 10mm', 59.99, 60, 'Yoga & Pilates', 'Ultra-cushioned yoga mat for joint protection. Perfect for restorative yoga and meditation.'),
    ('Cork Yoga Block Set of 2', 29.99, 110, 'Yoga & Pilates', 'Natural cork yoga blocks with beveled edges. Lightweight and eco-friendly.'),
    ('Yoga Strap with D-Ring 8ft', 14.99, 200, 'Yoga & Pilates', 'Cotton yoga strap with premium metal D-ring. Perfect for deepening stretches.'),
    ('Pilates Ring / Magic Circle', 34.99, 80, 'Yoga & Pilates', 'Pilates resistance ring with padded handles. For inner and outer thigh toning.'),
    ('Foam Roller 12" x 6" High Density', 39.99, 100, 'Yoga & Pilates', 'High-density EVA foam roller for muscle recovery and myofascial release.'),
    # Cardio Machines
    ('Foldable Treadmill with Incline', 599.99, 10, 'Cardio Machines', 'Motorized folding treadmill with 12 incline levels. Speed up to 12 km/h. LED display.'),
    ('Magnetic Exercise Bike Silent', 399.99, 15, 'Cardio Machines', 'Belt-driven magnetic resistance bike. Whisper-quiet operation. 8 resistance levels.'),
    ('Smart Rowing Machine', 449.99, 12, 'Cardio Machines', 'Air and magnetic hybrid rower with Bluetooth connectivity. Track your strokes and heart rate.'),
    ('Elliptical Cross-Trainer', 549.99, 8, 'Cardio Machines', 'Compact elliptical with 16 resistance levels. Smooth, low-impact full-body workout.'),
    ('Jump Rope Speed Cable – Bearing', 19.99, 250, 'Cardio Machines', 'Ball bearing speed jump rope with adjustable cable. Lightweight aluminum handles.'),
    # Home Gym Equipment
    ('Power Rack / Squat Stand', 299.99, 20, 'Home Gym Equipment', '7ft power rack with J-hooks and safety spotter arms. 1000lb weight capacity.'),
    ('Adjustable Weight Bench 0–90°', 199.99, 25, 'Home Gym Equipment', 'Flat, incline, decline adjustable bench with leg holder. Heavy-duty steel frame.'),
    ('FID Bench (Flat/Incline/Decline)', 259.99, 18, 'Home Gym Equipment', 'Professional FID bench with quick-adjust backrest. Supports up to 500kg.'),
    ('Pull-Up Bar Doorway', 34.99, 200, 'Home Gym Equipment', 'Door frame pull-up bar with foam grips. No drilling required. Supports up to 150kg.'),
    ('Dip Station Parallel Bars', 89.99, 40, 'Home Gym Equipment', 'Free-standing dip station with push-up handles. Non-slip rubber feet.'),
    ('Landmine Attachment', 44.99, 60, 'Home Gym Equipment', 'Floor-mounted landmine for rotational and press movements. Compatible with Olympic bars.'),
    # Fitness Accessories
    ('Ab Wheel Roller with Knee Pad', 19.99, 300, 'Fitness Accessories', 'Heavy-duty ab wheel with foam knee pad. Wide tire for stability on all surfaces.'),
    ('Push-Up Board Set', 24.99, 250, 'Fitness Accessories', 'Color-coded push-up board with 9 hand positions. Targets different muscle groups.'),
    ('Gymnastic Rings with Straps', 49.99, 75, 'Fitness Accessories', 'Wooden gymnastic rings with adjustable buckle straps. Supports up to 400kg.'),
    ('Weighted Vest 20kg Adjustable', 89.99, 30, 'Fitness Accessories', 'Adjustable weighted vest with iron sand filling. Even weight distribution.'),
    ('Battle Rope 50ft', 79.99, 20, 'Fitness Accessories', '50ft x 1.5" heavy duty battle rope for high-intensity conditioning drills.'),
    ('Slam Ball 10kg', 39.99, 45, 'Fitness Accessories', 'Rubber slam ball with textured grip. Bounces minimally for safe slams.'),
    # Gym Gloves & Straps
    ('Premium Gym Gloves – Ventilated', 24.99, 150, 'Gym Gloves & Straps', 'Breathing gym gloves with gel padding and wrist wrap. Anti-slip silicone palm.'),
    ('Heavy-Duty Lifting Straps', 14.99, 200, 'Gym Gloves & Straps', 'Cotton lifting straps for deadlifts and rows. 60cm length for secure wrapping.'),
    ('Figure-8 Lifting Straps', 19.99, 120, 'Gym Gloves & Straps', 'Figure-8 design for heavy pulls. Eliminates grip failure on max attempts.'),
    ('Wrist Wraps 12" – Pair', 16.99, 180, 'Gym Gloves & Straps', 'Elastic wrist wraps with thumb loop. 12" length for heavy pressing movements.'),
    ('Knee Sleeves 7mm – Pair', 39.99, 90, 'Gym Gloves & Straps', 'Neoprene knee sleeves for squatting support and joint warmth. 7mm thick.'),
    # Shaker Bottles & Blenders
    ('Classic Shaker Bottle 700ml', 12.99, 500, 'Shaker Bottles & Blenders', 'Leak-proof shaker bottle with mixing grid. BPA-free Tritan material.'),
    ('Stainless Steel Protein Shaker', 24.99, 200, 'Shaker Bottles & Blenders', 'Double-wall insulated steel shaker. Keeps drinks cold for 12 hours.'),
    ('Electric Bottle Shaker USB', 34.99, 100, 'Shaker Bottles & Blenders', 'USB rechargeable electric shaker with 3 mixing speeds. No more hand shaking!'),
    ('Portable Blender 600ml USB-C', 44.99, 80, 'Shaker Bottles & Blenders', 'Personal blender with USB-C charging. Blend smoothies anywhere. 6-blade system.'),
    ('Protein Shaker with Compartment', 18.99, 300, 'Shaker Bottles & Blenders', 'Shaker with built-in powder compartment and pill holder. Perfect for on-the-go.'),
    # Protein Supplements
    ('Whey Protein Isolate 2kg – Vanilla', 79.99, 60, 'Protein Supplements', '25g protein per serving, 0g fat. Premium cross-flow micro-filtered whey isolate.'),
    ('Whey Protein Isolate 2kg – Chocolate', 79.99, 55, 'Protein Supplements', 'Rich chocolate whey isolate with 25g protein per scoop. Mixes instantly.'),
    ('Whey Protein Isolate 2kg – Strawberry', 79.99, 45, 'Protein Supplements', 'Strawberry cream whey isolate. 25g protein, 110 calories per serving.'),
    ('Whey Protein Isolate 2kg – Cookies & Cream', 84.99, 40, 'Protein Supplements', 'Delicious cookies & cream flavor. 25g protein per serving, gluten-free.'),
    ('Plant Protein Powder 1kg – Chocolate', 54.99, 70, 'Protein Supplements', 'Vegan pea and rice protein blend. 22g protein per serving. Digestive enzymes added.'),
    ('Mass Gainer 3kg – Extreme', 69.99, 35, 'Protein Supplements', '1,250 calories, 50g protein per serving with creatine. For hard gainers.'),
    ('Whey Protein Concentrate 2kg – Unflavored', 49.99, 80, 'Protein Supplements', 'Pure unflavored whey concentrate. 24g protein per serving. Mix with anything.'),
    # BCAAs & Aminos
    ('BCAA 2:1:1 500g – Blue Raspberry', 34.99, 100, 'BCAAs & Aminos', 'Instantized BCAAs with glutamine. 5g BCAAs per serving. Zero sugar.'),
    ('BCAA 2:1:1 500g – Green Apple', 34.99, 90, 'BCAAs & Aminos', 'Crisp green apple BCAA formula. 5g BCAAs + electrolytes for hydration.'),
    ('EAAs 300g Complete', 29.99, 75, 'BCAAs & Aminos', 'All 9 essential amino acids with optimal ratios. Fast-absorbing.'),
    ('Glutamine 500g – Micronized', 29.99, 85, 'BCAAs & Aminos', 'Micronized L-glutamine for muscle recovery. Unflavored, dissolves easily.'),
    ('Beta-Alanine 200g', 19.99, 120, 'BCAAs & Aminos', 'Pure beta-alanine for muscular endurance. Reduces fatigue during high-rep sets.'),
    # Pre-Workout & Energy
    ('Pre-Workout 300g – Fruit Punch', 44.99, 80, 'Pre-Workout & Energy', 'High-stim pre-workout with 300mg caffeine, beta-alanine, and citrulline.'),
    ('Pre-Workout 300g – Lemon Lime', 44.99, 75, 'Pre-Workout & Energy', 'Explosive energy and focus with 320mg caffeine. Beta-alanine tingle guaranteed.'),
    ('Pre-Workout 300g – Blueberry', 44.99, 65, 'Pre-Workout & Energy', 'Blueberry flavored pre-workout with L-citrulline and agmatine for insane pumps.'),
    ('Stim-Free Pre-Workout 300g', 39.99, 50, 'Pre-Workout & Energy', 'Caffeine-free pump formula for evening workouts. L-citrulline + arginine.'),
    ('Energy Gummies 60 Pack', 24.99, 150, 'Pre-Workout & Energy', 'Caffeine energy gummies (100mg each). Tasty orange flavor. Easy to carry.'),
    ('Creatine Monohydrate 500g', 29.99, 200, 'Creatine & Mass Gainers', 'Micronized creatine monohydrate. 5g per serving. German quality.'),
    ('Creatine HCL 150 Capsules', 34.99, 100, 'Creatine & Mass Gainers', 'Creatine hydrochloride capsules. Better absorption, no bloating.'),
    ('Mass Gainer 5kg – Double Chocolate', 89.99, 25, 'Creatine & Mass Gainers', 'Ultra-premium mass gainer with 1,000 calories per serving. 50g protein.'),
    ('Lean Mass Gainer 2kg', 54.99, 40, 'Creatine & Mass Gainers', 'Low-sugar mass gainer for clean bulking. 600 calories, 40g protein per serving.'),
    # Vitamins & Wellness
    ('Multivitamin – 90 Tablets', 19.99, 300, 'Vitamins & Wellness', 'Complete daily multivitamin with minerals. 23 essential nutrients.'),
    ('Omega-3 Fish Oil 1000mg – 60 Caps', 24.99, 250, 'Vitamins & Wellness', 'Pharmaceutical-grade fish oil. 660mg EPA / 340mg DHA per serving.'),
    ('Vitamin D3 + K2 5000 IU – 60 Caps', 18.99, 200, 'Vitamins & Wellness', 'High-potency vitamin D3 with K2 for bone and immune health.'),
    ('Zinc Magnesium + B6 (ZMA) – 90 Caps', 24.99, 180, 'Vitamins & Wellness', 'Recovery formula with zinc, magnesium, and vitamin B6 for better sleep and anabolism.'),
    ('Magnesium Glycinate 400mg – 120 Caps', 29.99, 150, 'Vitamins & Wellness', 'Chelated magnesium glycinate for muscle relaxation and sleep support.'),
    # Fitness Apparel Men
    ('Men’s Gym T-Shirt – Compression Fit', 29.99, 200, 'Fitness Apparel – Men', 'Moisture-wicking compression tee with flatlock seams. 4-way stretch fabric.'),
    ('Men’s Gym Tank Top – Racerback', 24.99, 180, 'Fitness Apparel – Men', 'Sleeveless racerback tank for maximum mobility. Breathable mesh panels.'),
    ('Men’s Gym Shorts 7" Inseam', 34.99, 150, 'Fitness Apparel – Men', 'Training shorts with zippered pockets and inner brief. Lightweight and quick-dry.'),
    ('Men’s Joggers – Tapered Fit', 44.99, 120, 'Fitness Apparel – Men', 'Slim-fit joggers with zippered cuffs. Fleece lined for comfort.'),
    ('Men’s Hoodie – Full Zip', 59.99, 80, 'Fitness Apparel – Men', 'Full-zip gym hoodie with thumbhole cuffs. Two-layer hood for warmth.'),
    # Fitness Apparel Women
    ('Women’s High-Waisted Leggings', 44.99, 180, 'Fitness Apparel – Women', 'High-waist compression leggings with hidden waistband pocket. Squat-proof fabric.'),
    ('Women’s Sports Bra – Medium Support', 34.99, 160, 'Fitness Apparel – Women', 'Medium-impact sports bra with adjustable straps. Moisture-wicking and soft.'),
    ('Women’s Gym Crop Top', 29.99, 140, 'Fitness Apparel – Women', 'Cropped length with wide hem band. Breathable fabric for intense workouts.'),
    ('Women’s Training Shorts 5"', 32.99, 120, 'Fitness Apparel – Women', 'Comfort-fit training shorts with elastic waist and inner liner.'),
    ('Women’s Yoga Pants – Flare', 49.99, 90, 'Fitness Apparel – Women', 'Flare-bottom yoga pants with tummy control waistband. Stretchy and soft.'),
    # Footwear
    ('Men’s Training Shoes – CrossFit', 129.99, 40, 'Footwear', 'Versatile training shoes with wide toe box. Rope guard and heel stability clip.'),
    ('Men’s Running Shoes – Cushion', 119.99, 50, 'Footwear', 'Maximum cushion running shoe with responsive foam. Breathable mesh upper.'),
    ('Women’s Training Shoes – Studio', 109.99, 35, 'Footwear', 'Studio training shoes with non-marking sole. Flexible for all group fitness.'),
    ('Women’s Running Shoes – Lightweight', 99.99, 45, 'Footwear', 'Lightweight running shoe with energy return midsole. Perfect for daily runs.'),
    ('Flip Flops – Post Workout', 19.99, 300, 'Footwear', 'Durable EVA flip flops with arch support. Quick-dry and easy to clean.'),
    # Gym Bags
    ('Duffel Gym Bag 50L', 49.99, 70, 'Gym Bags & Backpacks', 'Large duffel bag with wet/dry compartment. Shoe pocket and padded shoulder strap.'),
    ('Backpack Gym Bag 30L', 44.99, 90, 'Gym Bags & Backpacks', 'Gym backpack with laptop sleeve and ventilated shoe compartment. Ergonomic design.'),
    ('String Gym Sack / Drawstring', 14.99, 400, 'Gym Bags & Backpacks', 'Lightweight drawstring bag with small zipper pocket. Perfect for essentials.'),
    ('Premium Leather Gym Bag', 89.99, 25, 'Gym Bags & Backpacks', 'Vintage leather duffel with brass hardware. Spacious main compartment.'),
    # Jump Ropes & Speed Ropes
    ('Speed Jump Rope – Bearing System', 24.99, 200, 'Jump Ropes & Speed Ropes', 'Professional speed rope with dual ball bearings. Adjustable 3m cable.'),
    ('Weighted Jump Rope 500g', 29.99, 120, 'Jump Ropes & Speed Ropes', 'Weighted rope for upper body engagement. 500g handles for added resistance.'),
    ('Beaded Jump Rope – Beginner', 19.99, 300, 'Jump Ropes & Speed Ropes', 'Colorful beaded jump rope for rhythm and timing. Great for beginners and kids.'),
    ('Jump Rope Mat – Non-Slip', 34.99, 80, 'Jump Ropes & Speed Ropes', 'Protective jump rope mat 6mm thick. Shock absorbing and non-slip surface.'),
]

# ─── Seller / Store data ─────────────────────────────────────
SELLERS = [
    ('fitspire', 'FitSpire Sports', 'individual', 'Premium fitness equipment sourced from top manufacturers worldwide. Quality guaranteed.'),
    ('ironparadise', 'Iron Paradise', 'company', 'Iron Paradise has been supplying gyms across the country with professional-grade weights and machines since 2018.'),
    ('flexhouse', 'FlexHouse Nutrition', 'company', 'Science-backed sports nutrition supplements. Third-party tested for purity and potency.'),
    ('ayurvedafit', 'AyurvedaFit', 'individual', 'Natural fitness supplements inspired by ancient wellness traditions. Herbal and effective.'),
    ('gymwearpro', 'GymWear Pro', 'company', 'Designed for performance. Our apparel is worn by athletes in over 30 countries.'),
    ('cardiolife', 'CardioLife', 'individual', 'Affordable cardio machines for home and commercial use. Assembly and support included.'),
]

# ─── Run Seeding ─────────────────────────────────────────────
def seed():
    print("🌱 Seeding realistic e-commerce data...\n")

    # ──── 1. Admin user ────
    admin, _ = User.objects.get_or_create(username='jeevan', defaults={'email': 'jeevan@admin.com', 'is_staff': True, 'is_superuser': True})
    admin.set_password('REPLACED_ADMIN_PASS')
    admin.save()
    prof, _ = Profile.objects.get_or_create(user=admin)
    prof.is_seller = True
    prof.store_name = 'FitnessHub Official'
    prof.phone = '+977-9812345678'
    prof.address_line1 = 'Kathmandu, Nepal'
    prof.save()
    print(f"  ✓ Admin: jeevan / REPLACED_ADMIN_PASS")

    # ──── 2. Categories (look up existing curated categories) ────
    for cat_name, cat_id in CATEGORY_IDS.items():
        obj = Category.objects.get(id=cat_id)
        cat_objects[cat_name] = obj
    print(f"  ✓ {len(CATEGORY_IDS)} categories mapped")

    # ──── 3. Seller Users ────
    seller_users = []
    for username, store, btype, desc in SELLERS:
        u, created = User.objects.get_or_create(username=username, defaults={'email': f'{username}@{store.lower().replace(" ","")}.com'})
        u.set_password('seller123')
        u.save()
        p, _ = Profile.objects.get_or_create(user=u)
        p.is_seller = True
        p.seller_requested = False
        p.store_name = store
        p.store_slug = slugify(store)
        p.business_type = btype
        p.store_description = desc
        p.phone = f'+1-555-{random.randint(1000,9999)}'
        p.save()
        seller_users.append(u)
        print(f"  ✓ Seller: {store} (@{username}) / seller123")

    # ──── 4. Products ────
    product_objects = []
    for name, price, stock, cat, desc in PRODUCTS:
        seller = random.choice(seller_users)
        obj = Product.objects.create(
            name=name,
            price=price,
            stock=stock,
            description=desc,
            category=cat_objects[cat],
            seller=seller,
            is_featured=random.random() < 0.15,
            is_sale=random.random() < 0.10,
            created_at=rand_date(120),
        )
        # Some products get sizes
        if random.random() < 0.20:
            sizes = random.sample(['S', 'M', 'L', 'XL', 'XXL'], random.randint(2, 4))
            for sz in sizes:
                ProductSize.objects.create(product=obj, size=sz, stock=random.randint(5, 30))
            obj.size = ','.join(sizes)
            obj.stock = 0
            obj.save(update_fields=['size', 'stock'])
        product_objects.append(obj)
    print(f"  ✓ {len(PRODUCTS)} products created")

    # ──── 5. Regular Users ────
    first_names = ['Alex', 'Jordan', 'Taylor', 'Morgan', 'Casey', 'Riley', 'Avery', 'Quinn', 'Mason', 'Liam',
                   'Emma', 'Sophia', 'Olivia', 'Ethan', 'Noah', 'Aria', 'Luna', 'Mia', 'Zara', 'Kai',
                   'Sebastian', 'Mateo', 'Leo', 'Elijah', 'Rohan', 'Priya', 'Anika', 'Arjun', 'Mei', 'Yuki',
                   'Sam', 'Charlie', 'Drew', 'Blake', 'Hayden', 'Finley', 'Rowan', 'Skyler', 'Parker', 'Reese',
                   'Aadhya', 'Vihaan', 'Ishaan', 'Sara', 'Aisha', 'Omar', 'Fatima', 'Jamal', 'Zainab', 'Hassan']
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez',
                  'Hernandez', 'Lopez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Lee', 'Wang', 'Chen', 'Kim',
                  'Patel', 'Shah', 'Kumar', 'Singh', 'Gupta', 'Joshi', 'Thapa', 'Rai', 'Gurung', 'Tamang',
                  'Al-Farsi', 'Sato', 'Tanaka', 'Nakamura', 'Watanabe', 'Okafor', 'Nwachukwu', 'Okonkwo', 'Kone', 'Diop']
    product_pool = list(Product.objects.all())
    product_ids = [p.id for p in product_pool]

    regular_users = []
    num_users = min(50, len(first_names) * 2)
    used_usernames = set()

    for i in range(num_users):
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        base = f"{fn.lower()}.{ln.lower()}"
        username = base
        while username in used_usernames:
            username = f"{base}{random.randint(1,99)}"
        used_usernames.add(username)
        email = f"{username}@email.com"
        u = User.objects.create_user(username=username, email=email, password='user123')
        u.date_joined = rand_date(90)
        u.save()
        p, _ = Profile.objects.get_or_create(user=u)
        p.phone = f'+1-555-{random.randint(1000,9999)}'
        p.address_line1 = f'{random.randint(1,9999)} {random.choice(["Oak", "Maple", "Elm", "Cedar", "Pine", "Main", "Park", "Lake", "Hill", "River"])} {random.choice(["St", "Ave", "Blvd", "Dr", "Ln", "Way", "Rd"])}'
        p.city = random.choice(['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'Austin', 'Portland', 'Seattle', 'Denver', 'Miami', 'Boston'])
        p.state = random.choice(['NY', 'CA', 'TX', 'FL', 'IL', 'PA', 'OH', 'GA', 'NC', 'MI'])
        p.zip_code = f'{random.randint(10000,99999)}'
        p.country = 'US'
        p.save()
        regular_users.append(u)

    print(f"  ✓ {num_users} regular users created (password: user123)")

    # ──── 6. Favorites ────
    fav_count = 0
    for u in regular_users:
        num_favs = random.randint(0, 12)
        chosen = random.sample(product_ids, min(num_favs, len(product_ids)))
        for pid in chosen:
            _, created = FavoriteItem.objects.get_or_create(user=u, product_id=pid,
                                                            defaults={'created_at': rand_date(60)})
            if created:
                fav_count += 1
    print(f"  ✓ {fav_count} favorites")

    # ──── 7. Cart Items ────
    cart_count = 0
    for u in regular_users[:35]:  # Not all have active carts
        num_items = random.randint(0, 5)
        chosen = random.sample(product_ids, min(num_items, len(product_ids)))
        for pid in chosen:
            prod = Product.objects.get(id=pid)
            qty = random.randint(1, 3)
            sz = None
            if prod.has_sizes:
                sz = random.choice(list(prod.sizes.values_list('size', flat=True)))
            _, created = CartItem.objects.get_or_create(
                user=u, product=prod, size=sz or '',
                defaults={'quantity': qty, 'added_at': rand_date(14)}
            )
            if created:
                cart_count += 1
    print(f"  ✓ {cart_count} cart items")

    # ──── 8. Orders + OrderItems ────
    order_count = 0
    order_item_count = 0
    statuses = ['Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled']
    status_weights = [15, 10, 10, 45, 20]

    for u in regular_users:
        num_orders = random.randint(0, 6)
        for _ in range(num_orders):
            status = pick_weighted(list(zip(status_weights, statuses)))
            created = rand_date(60)
            num_items = random.randint(1, 5)
            items_list = random.sample(product_ids, min(num_items, len(product_ids)))
            total = 0
            order = Order.objects.create(
                user=u,
                order_number=uuid.uuid4().hex[:10].upper(),
                full_name=f"{random.choice(first_names)} {random.choice(last_names)}",
                email=u.email,
                shipping_address=f"{random.randint(1,9999)} {random.choice(['Oak','Maple','Elm','Cedar'])} {random.choice(['St','Ave','Blvd'])}, {random.choice(['New York','Los Angeles','Chicago'])}",
                total_amount=0,
                status=status,
                created_at=created,
            )
            for pid in items_list:
                prod = Product.objects.get(id=pid)
                qty = random.randint(1, 3)
                sz = None
                if prod.has_sizes and random.random() < 0.5:
                    sz = random.choice(list(prod.sizes.values_list('size', flat=True)))
                item_total = float(prod.price) * qty
                OrderItem.objects.create(
                    order=order, product=prod, size=sz or None,
                    price=prod.price, quantity=qty,
                )
                total += item_total
                order_item_count += 1
            order.total_amount = round(total, 2)
            order.save(update_fields=['total_amount'])
            order_count += 1

    print(f"  ✓ {order_count} orders, {order_item_count} order items")

    # ──── 9. Reviews ────
    review_count = 0
    for u in regular_users:
        reviewed = set()
        for _ in range(random.randint(0, 4)):
            pid = random.choice(product_ids)
            if pid in reviewed:
                continue
            reviewed.add(pid)
            rating = random.choices([5, 4, 3, 2, 1], weights=[40, 30, 15, 10, 5])[0]
            comments = [
                '', '', '',
                'Great product, exceeded expectations!',
                'Exactly what I needed. Fast shipping.',
                'Good quality for the price.',
                'Works perfectly, highly recommend.',
                'Solid build quality, would buy again.',
                'Decent product but packaging could be better.',
                'Not what I expected, but it\'s okay.',
                'Exactly as described. Very happy.',
                'Best purchase this month!',
                'My go-to brand now. Love it.',
                'Good but a bit overpriced.',
                'Perfect for my home gym setup.',
                'Fits well and comfortable.',
            ]
            Review.objects.create(
                user=u, product_id=pid,
                rating=rating,
                comment=random.choice(comments),
                created_at=rand_date(90),
            )
            review_count += 1
    print(f"  ✓ {review_count} reviews")

    # ──── 10. Update product ratings ────
    from django.db.models import Avg
    for p in Product.objects.all():
        avg = Review.objects.filter(product=p).aggregate(Avg('rating'))['rating__avg']
        if avg:
            Product.objects.filter(id=p.id).update(rating=round(avg, 1))
    print(f"  ✓ Product ratings updated")

    # ──── Summary ────
    print(f"\n{'='*50}")
    print(f"  Seeding Complete!")
    print(f"{'='*50}")
    print(f"  Admin:     jeevan / REPLACED_ADMIN_PASS")
    print(f"  Sellers:   {len(seller_users)} (password: seller123)")
    print(f"  Users:     {len(regular_users)} (password: user123)")
    print(f"  Products:  {Product.objects.count()}")
    print(f"  Orders:    {Order.objects.count()}")
    print(f"  Reviews:   {Review.objects.count()}")
    print(f"  Favorites: {FavoriteItem.objects.count()}")
    print(f"  Cart:      {CartItem.objects.count()}")
    print(f"{'='*50}")


if __name__ == '__main__':
    seed()
