// Initiate global websocket object.
// @todo: Dirty hack to send the cookie....
var ws = new WebSocket("ws://127.0.0.1:8888/socket");

/**
 * Helper function to get the calue of a cookie. We use this to send _xsrf
 * token which is stored in a cookie.
 * @param name The name of the cookie.
 * @returns
 */

function cookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function() {
    if (!window.console) window.console = {};
    if (!window.console.log) window.console.log = function() {};

    // Bin submit event to postMessage().
    $("#chat-input").submit(function() {
        postMessage($(this));
        return false;
    });
    // Bind pressing enter event to postMessage().
    $("#chat-input").live("keypress", function(e) {
        if (e.keyCode == 13) {
            postMessage($(this));
            return false;
        }
    });
    $("#message-input").focus();
    $('html, body').animate({scrollTop: $(document).height()}, 800);
    
    // Connection state should be reflacted in submit button.
    var disabled = $("form#chat-input").find("input");
    disabled.attr("disabled", "disabled");
    
    ws.onopen = function() {
        console.log("Connected...");
        disabled.removeAttr("disabled");
    };
    ws.onmessage = function(event) {
        data = JSON.parse(event.data);
        if(data.textStatus && data.textStatus == "unauthorized") {
            alert("unauthorized");
            disabled.attr("disabled", "disabled");
        }
        else if(data.error && data.textStatus) {
            alert(data.textStatus);
        }
        console.log("New Message", data);
        if (data.messages) newMessages(data);
    };
    ws.onclose = function() {
        // @todo: Implement reconnect.
        console.log("Closed!");
        disabled.attr("disabled", "disabled");
    };
});

/**
 * Function to create a new message.
 * @param form The form beeing submitted.
 */
function postMessage(form) {
    var value = form.find("input[type=text]").val();
    var message = {body: value};
    message._xsrf = cookie("_xsrf");
    var disabled = form.find("input");
    disabled.attr("disabled", "disabled");
    // Send message using websocket.
    ws.send(JSON.stringify(message));
    // @todo: A response if successful would be nice. 
    console.log("Created message (successfuly)");
    $("#message-input").val("").select();
    disabled.removeAttr("disabled");
}

updater = {}

/**
 * Callback when receiving new messages.
 */
newMessages = function (data) {
    var messages = data.messages;
    if(messages.length == 0) return;
    updater.cursor = messages[messages.length - 1]._id;
    console.log(messages.length + "new messages, cursor: " + updater.cursor);
    for (var i = 0; i < messages.length; i++) {
        showMessage(messages[i]);
    }
};

/**
 * Function to add a bunch of (new) messages to the inbox.
 */
showMessage = function(message) {
    console.log("Show Message");
    var existing = $("#m" + message._id);
    if (existing.length > 0) return;
    $("#messsages").append('<div style="display: none;" class="message" id="' + message._id + '"><b>' + message.from + ': </b>' + message.body + '</div>');
    $('#messsages').find(".message:last").slideDown("fast", function(){
        $('html, body').animate({scrollTop: $(document).height()}, 400);
    });
};
