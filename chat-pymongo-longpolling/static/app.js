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
    updater.poll();
});

/**
 * Function to create a new message.
 * @param form The form beeing submitted.
 */
function postMessage(form) {
    var value = form.find("input[type=text]").val();
    var message = {body: value};
    message._xsrf = cookie("_xsrf");
    var disabled = form.find("input[type=submit]");
    disabled.attr("disabled", "disabled");
    // Send an ajax request with the messagae as payload.
    $.ajax({
        url: "/message",
        data: $.param(message),
        dataType: "json",
        type: "POST",
        //contentType: 'application/json',
        timeout: 60000,
        cache: false
    }).done(function ( data ) {
        if (!data._id) {
            console.log("Error creating message");
            $("#message-input").select();
        }
        else {
            console.log("Created message successfuly");
            $("#message-input").val("").select();
        }
        disabled.removeAttr("disabled");
    }).fail(function(jqXHR, textStatus) {
        console.log("Error creating message: " + textStatus);
        disabled.removeAttr("disabled");
        $("#message-input").select();
    });
}


/**
 * Object implementing long polling, receiving and displaying new messages.
 */
var updater = {
    errorSleepTime: 500,
    cursor: null,

    /**
     * Performs the long polling request. Is recalled when finished.
     */
    poll: function() {
        var data = {"_xsrf": cookie("_xsrf")};
        if (updater.cursor) data.cursor = updater.cursor;
        // Send an ajax request with the cursor as payload.
        $.ajax({
            url: "/message",
            data: $.param(data),
            dataType: "json",
            type: "GET",
            //contentType: 'application/json',
            timeout: 60000,
            cache: false
        }).done(function ( data ) {
            if (!data.messages) {
                console.log("Error Receiving new messages");
                return;
            }
            console.log("Received new messages successfuly");
            updater.newMessages(data);
            updater.errorSleepTime = 500;
            window.setTimeout(updater.poll, 0);
        }).fail(function(jqXHR, textStatus) {
            updater.errorSleepTime *= 2;
            console.log("Poll error " + textStatus + "; sleeping for " + updater.errorSleepTime + " ms");
            window.setTimeout(updater.poll, updater.errorSleepTime);
        });
    },

    /**
     * Callback when polling receive new messages.
     */
    newMessages: function (data) {
        var messages = data.messages;
        updater.cursor = messages[messages.length - 1]._id;
        console.log(messages.length + "new messages, cursor: " + updater.cursor);
        for (var i = 0; i < messages.length; i++) {
            updater.showMessage(messages[i]);
        }
    },

    /**
     * Function to add a bunch of (new) messages to the inbox.
     */
    showMessage: function(message) {
        console.log("Show Message");
        var existing = $("#m" + message._id);
        if (existing.length > 0) return;
        $("#messsages").append('<div style="display: none;" class="message" id="' + message._id + '"><b>' + message.from + ': </b>' + message.body + '</div>');
        $('#messsages').find(".message:last").slideDown("fast", function(){
            $('html, body').animate({scrollTop: $(document).height()}, 400);
        });
    }
};
