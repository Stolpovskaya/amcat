task = (function(uuid){
    self = this;

    var task_api = "/api/v4/task?uuid=" + uuid;
    var taskresult_api = "/api/v4/taskresult/" + uuid;

    // Initial timeout in milliseconds. Will increase half a second for
    // every poll, with an upper limit of 3 seconds.
    var timeout = 200;

    /*
     * Po
     */
    function poll(timeout){
        $.ajax({
            url: task_api,
            dataType: 'json',
            success: poll_success,
            error: poll_error
        })
    }

    function poll_error(){
        $("#status").text("Polling failed. Refresh?");
    }

    function poll_success(data){
        timeout = (timeout >= 3000) ? timeout : timeout + 500;

        var task = data["results"][0];
        if (!task.ready && task.status === "INPROGRESS" && task.progress !== null){
            // Not yet ready, progress indication supplied
            window.setTimeout(poll, timeout);
        } else if (!task.ready){
            // Not yet ready, but no progress indiction supplied also
            window.setTimeout(poll, timeout);
        } else if (task.ready && task.status != "SUCCESS") {
            // Task ready, but failed.
            task_failed(task);
        } else {
            // Task ready and available for download
            task_success(task);
        }

        update_progress(task);
    }

    function update_progress(task){
        $("#status").text(task.status);

        if (task.progress !== null){
            $("#message").text(task.message);
            $("#progress").text(task.progress);
        }
    }

    function task_failed(task){
        console.log("failed")
    }

    function task_success(task){
        $(".hide-if-success").hide();
        $("#results").show();
    }

    poll();
});