// ==============================================================================
// File: messages.js
// Description: Polls unread message count every 5 seconds
// ==============================================================================

// ==============================================================================
// SECTION: Unread Count Polling
// ==============================================================================

(function(){
    var badge = document.getElementById('msg-badge');
    if (!badge) return;
    function check(){
        var xhr = new XMLHttpRequest();
        xhr.open('GET', '/store/api/messages/unread/', true);
        xhr.onload = function(){
            if(xhr.status !== 200) return;
            try {
                var data = JSON.parse(xhr.responseText);
                if(data.unread > 0){
                    badge.textContent = data.unread;
                    badge.style.display = 'inline';
                } else {
                    badge.style.display = 'none';
                }
            } catch(e){}
        };
        xhr.send();
    }
    check();
    setInterval(check, 5000);
})();
