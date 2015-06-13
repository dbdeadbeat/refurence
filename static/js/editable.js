$(function () {
    function getGalleryTableTabs() {
        var gallery_tabs = document.querySelectorAll(".gallery_table_tab_name");
        var out = [];
        for (var idx = 0; idx < gallery_tabs.length; idx++) {
            out[idx] = gallery_tabs[idx].text;
        }
        return out;
    }

    function getActiveGalleryTabName() {
        return document.querySelector('.active.gallery_tab_li').children[0].text;
    }

    function getActiveGalleryNum () {
        var sel = $('.active.tab-pane').attr('id');
        var toks = sel.split('-');
        return toks[toks.length-1];
    }

    function createDescriptionDropZone(div_id) {
        var myDropzone = new Dropzone('#' + div_id, {
            url: "/upload/",
            method: "POST", // can be changed to "put" if necessary
            paramName: "file", // The name that will be used to transfer the file
            uploadMultiple: true, // This option will also trigger additional events (like processingmultiple).
            addRemoveLinks: false, // add an <a class="dz-remove">Remove file</a> element to the file preview that will remove the file, and it will change to Cancel upload
            createImageThumbnails: true,
            maxThumbnailFilesize: 2, // in MB
            thumbnailWidth: 300,
            thumbnailHeight: 300,
            maxFiles: 1,
            acceptedFiles: "image/png, image/jpeg, image/gif", //This is a comma separated list of mime types or file extensions.Eg.: image/*,application/pdf,.psd.
            autoProcessQueue: true, // When set to false you have to call myDropzone.processQueue() yourself in order to upload the dropped files. 
            forceFallback: false,
        });

        myDropzone.on("success", function(file, response) {
            var toks = div_id.split('-');
            var num = toks[toks.length-1];
            Sijax.request('add_image_to_description', [ {'num': num, 'files': response['files']} ], {'async': false});
        });

        myDropzone.on("complete", function(file) {
            myDropzone.removeAllFiles();
            refreshDescriptionDropZones();
        });

    }

    function refreshDescriptionDropZones() {
        var descriptionDrops = $('.description-drop');
        for (var idx = 0; idx < descriptionDrops.length; idx++)
            createDescriptionDropZone($(descriptionDrops[idx]).attr('id'));
    }

    function createGalleryDropZone(div_id) {
        var myDropzone = new Dropzone('#' + div_id, {
            url: "/upload/",
            method: "POST", // can be changed to "put" if necessary
            paramName: "file", // The name that will be used to transfer the file
            uploadMultiple: true, // This option will also trigger additional events (like processingmultiple).
            addRemoveLinks: false, // add an <a class="dz-remove">Remove file</a> element to the file preview that will remove the file, and it will change to Cancel upload
            createImageThumbnails: true,
            maxThumbnailFilesize: 2, // in MB
            thumbnailWidth: 300,
            thumbnailHeight: 300,
            acceptedFiles: "image/png, image/jpeg, image/gif", //This is a comma separated list of mime types or file extensions.Eg.: image/*,application/pdf,.psd.
            autoProcessQueue: true, // When set to false you have to call myDropzone.processQueue() yourself in order to upload the dropped files. 
            forceFallback: false,
        });

        myDropzone.on("successmultiple", function(files, response) {
            var toks = div_id.split('-');
            var num = toks[toks.length-1];

            for (var idx = 0; idx < files.length; idx++) {
                myDropzone.removeFile(files[idx]);
            }

            Sijax.request('add_image_to_gallery', [{
                'num': num,
                'files': response['files']
            }]
            );
        });
    }

    function refreshGalleryDropZones() {
        var galleryDrops = $('.gallery-drop');
        for (var idx = 0; idx < galleryDrops.length; idx++) {
            createGalleryDropZone($(galleryDrops[idx]).attr('id'));
        }
    }

    function createAvatarDropZone(div_id) {
        var myDropzone = new Dropzone('#' + div_id, {
            url: "/upload/",
            method: "POST",
            paramName: "file",
            uploadMultiple: false,
            addRemoveLinks: false,
            createImageThumbnails: true,
            maxThumbnailFilesize: 2,
            thumbnailWidth: 128,
            thumbnailHeight: 128,
            maxFiles: 1,
            acceptedFiles: "image/png, image/jpeg, image/gif",
            autoProcessQueue: true,
            forceFallback: false,
        });

        myDropzone.on("success", function(file, response) {
            Sijax.request('update_avatar_url', [ { 
                'files': response['files']
            }
            ]);
        });

        myDropzone.on("complete", function(file) {
            myDropzone.removeAllFiles();
        });

    }

    function createBkgDropZone(div_id) {
        var myDropzone = new Dropzone('#' + div_id, {
            url: "/upload/",
            method: "POST",
            paramName: "file",
            uploadMultiple: false,
            addRemoveLinks: false,
            createImageThumbnails: true,
            maxThumbnailFilesize: 2,
            thumbnailWidth: 128,
            thumbnailHeight: 128,
            maxFiles: 1,
            acceptedFiles: "image/png, image/jpeg, image/gif",
            autoProcessQueue: true,
            forceFallback: false,
        });

        myDropzone.on("success", function(file, response) {
            Sijax.request('change_bkg_dropbox', [ {
                'files': response['files']
            } ]);
        });

        myDropzone.on("complete", function(file) {
            myDropzone.removeAllFiles();
        });

    }

    $('#btn_discard').bind('click', function() {
        Sijax.request('discard_changes', [ { } ]);
        return false;
    });

    // image link popovers
    $('body').on('click', '.btn-editable-imglink', function (e) {
        $(this).popover('show');
    });

    $('body').on('keydown', '[contenteditable="True"]', function (e) {
        var target = $(e.currentTarget);
        if (e.keyCode === 13) {
            if (target.attr('class') == 'panel-heading') {
                return false;
            }
        }

        var selection = window.getSelection(),
        range = selection.getRangeAt(0);
        br = document.createTextNode('\n');
        range.deleteContents();
        range.insertNode(br);
        range.setStartAfter(br);
        range.setEndAfter(br);
        range.collapse(false);
        selection.removeAllRanges();
        selection.addRange(range);

        return false;
    }

    $('a').on('keydown', function (e) {
        var target = $(e.currentTarget);
        if (e.keyCode === 13) {
            if (target.attr('class').includes('gallery_table_tab_name'))
        return false;
        }
    });

    $('a').on('paste', function (e) {
        var target = $(e.currentTarget);
        if (target.attr('class').includes('gallery_table_tab_name'))
        return false;
    });

    $('body').on('paste', '[contenteditable="True"]', function (evt) {
        var thisclass = $(this).attr("class");
        if (thisclass == 'panel-heading' || thisclass == 'btn' || thisclass == 'gallery_table_tab_name') {
            return false;
        }

        if(evt.originalEvent.clipboardData || window.clipboardData)  {
            evt.preventDefault();
            //webkit (and bleeding edge Firefox)
            var selection = window.getSelection ? window.getSelection() : document.selection;
            var range = selection.getRangeAt ? selection.getRangeAt(0) : selection.createRange();

            //prepare new range selection

            var startingCaretPosition = range.startOffset;

            //place the pasted content at the cursor position within
            //the div
            var $target = $(evt.target);
            var clipboard = evt.originalEvent.clipboardData ? evt.originalEvent.clipboardData.getData("text/plain") :
        window.clipboardData.getData("Text");
            var newText = $target.text().substring(0,range.startOffset) +
                clipboard +
                $target.text().substring(range.endOffset,$target.text().length);
            $target.text(newText);

            //create a new selection range so that the cursor is at the end
            //of the newly pasted content
            var targetNode = evt.target;
            if(window.getSelection) { // webkit
                if(evt.target.childNodes.length > 0)
                    targetNode = evt.target.childNodes[0];
                var newRange = document.createRange();
                newRange.setStart(targetNode,startingCaretPosition+clipboard.length);
                newRange.setEnd(targetNode,startingCaretPosition+clipboard.length);
                if(selection.rangeCount > 0) selection.removeAllRanges();
                selection.addRange(newRange);
            } else { //IE
                if(evt.target.childNodes.length > 0) targetNode = evt.target.childNodes[0];

                var newRange = document.selection.createRange();
                newRange.moveToElementText(evt.target);
                newRange.setStart(targetNode,startingCaretPosition+clipboard.length);
                newRange.setEnd(targetNode,startingCaretPosition+clipboard.length);
                newRange.select();
            }
        }
    });

    // hide popover if click elsewhere on page
    $('body').on('click', function (e) {
        $('[data-toggle="popover"]').each(function () {
            if (!$(this).is(e.target) && $(this).has(e.target).length === 0 && $('.popover').has(e.target).length === 0) {
                $(this).popover('hide');
            }
        });
    });

    $('button#btn_gallery_add').on('click', function() {
        Sijax.request('add_gallery', [ {} ], {'async': false});
        refreshGalleryDropZones();
    });
    $('button#btn_gallery_del').on('click', function() {
        Sijax.request('del_gallery', [ { active : getActiveGalleryNum() } ],
            {'async': false});
        refreshGalleryDropZones();
    });
    $('body').on('click', '.btn_gallery_del_img', function() {
        Sijax.request('gallery_del_image', [ {
            active : getActiveGalleryNum(),
            url : this.children[0].href,
        }]
        );
    });

    Dropzone.autoDiscover = false;

    refreshDescriptionDropZones();
    refreshGalleryDropZones();
    createAvatarDropZone('avatar-drop');
    createBkgDropZone('bkg-drop');

});
