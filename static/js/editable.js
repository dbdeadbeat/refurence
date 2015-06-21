$(function () {

    function br2nl(str) {
        return str.replace(/<br>/mg,"\n");
    }

    function getDescriptionTable() {
        var titles = $('.description-title');
        var bodies = $('.description-body');
        var out = {};
        for (var idx = 0; idx < titles.length; idx++) {
            var header = $(titles[idx]);
            var body = $(bodies[idx]);

            header = br2nl(header.html());
            header = header.replace(/(\r\n|\n|\r)/gm,"");
            header = header.replace(/^\s+|\s+$/g, '');

            body = br2nl(body.html());
            out[header] = {'order': idx, 'text': body};
        }
        return out;
    }

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

    function resizeMasonry() {
        var gutter = parseInt($('.post').css('marginBottom'));
        var container = $('.posts');
        if (!$('.posts').parent().hasClass('container')) {
            post_width = $('.post').width() + gutter;
            $('.posts, body > #grid').css('width', 'auto');
            posts_per_row = $('.posts').innerWidth() / post_width;
            floor_posts_width = (Math.floor(posts_per_row) * post_width) - gutter;
            ceil_posts_width = (Math.ceil(posts_per_row) * post_width) - gutter;
            posts_width = (ceil_posts_width > $('.posts').innerWidth()) ? floor_posts_width : ceil_posts_width;
            if (posts_width == $('.post').width()) {
                posts_width = '100%';
            }
        }
    }

    function refreshMasonry() {
        $('.posts').imagesLoaded( function () {
            var gutter = parseInt(jQuery('.post').css('marginBottom'));
            var container = jQuery('.posts');
            container.masonry({
                gutter: gutter,
                itemSelector: '.post',
                columnWidth: '.post'
            });
        });  

        $('a[data-toggle="tab"]').each(function () {
            var $this = $(this);
            var $container = $('.posts');

            $this.on('shown.bs.tab', function () {
                $container.imagesLoaded( function () {
                    refreshMasonry();
                });  
            });
        });
    }

    function createDescriptionDropZone(div_id) {
        var myDropzone = new Dropzone('#' + div_id, {
            url: "/upload/",
            method: "POST",
            paramName: "file",
            uploadMultiple: true,
            addRemoveLinks: false,
            createImageThumbnails: true,
            maxThumbnailFilesize: 2,
            maxFiles: 1,
            thumbnailWidth: 300,
            thumbnailHeight: 300,
            acceptedFiles: "image/png, image/jpeg, image/gif",
            autoProcessQueue: true,
            forceFallback: false,
        });

        myDropzone.on("success", function(file, response) {
            var toks = div_id.split('-');
            var num = toks[toks.length-1];
            Sijax.request('add_image_to_description', [ {'num': num, 'files': response['files']} ], {'async': false});
        });

        myDropzone.on("complete", function(file) {
            myDropzone.removeAllFiles();
            refreshDescriptionJS();
        });

    }

    function refreshDescriptionJS() {
        var descriptionDrops = $('.description-drop');
        for (var idx = 0; idx < descriptionDrops.length; idx++)
            createDescriptionDropZone($(descriptionDrops[idx]).attr('id'));

        $('.btn-delete-description').bind('click', function() {
            var id = $(this).attr('id');
            var toks = id.split('-');
            id = parseInt(toks[toks.length-1]);
            Sijax.request('del_desc_table', [{
                num: id,
                'desc_table': getDescriptionTable()
            }],
            {'async': false});
            refreshDescriptionJS();
        });

        refreshMasonry();
    }

    function createGalleryDropZone(div_id) {
        var myDropzone = new Dropzone('#' + div_id, {
            url: "/upload/",
            method: "POST",
            paramName: "file",
            uploadMultiple: true,
            addRemoveLinks: false,
            createImageThumbnails: true,
            maxThumbnailFilesize: 2,
            thumbnailWidth: 300,
            thumbnailHeight: 300,
            acceptedFiles: "image/png, image/jpeg, image/gif",
            autoProcessQueue: true,
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
                }],
                {
                    'complete': function() {
                        refreshMasonry();
                    }
                }
            );
        });

        myDropzone.on("queuecomplete", function(files, response) {
            refreshMasonry();
        });
    }

    function refreshGalleryJS() {
        var galleryDrops = $('.gallery-drop');
        for (var idx = 0; idx < galleryDrops.length; idx++) {
            createGalleryDropZone($(galleryDrops[idx]).attr('id'));
        }
        refreshMasonry();
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

    $('button#btn_sidebar_add_link').on('click', function() {
        Sijax.request('add_imglink', [ {} ]);
    });
    $('button#btn_gallery_add').on('click', function() {
        $('#gallery-editable').block({ 
            message: '<h3>processing...</h3>', 
            css: { } 
        }); 
        Sijax.request('add_gallery', [ {} ],
            {
                'complete': function() {
                    $('#gallery-editable').unblock();
                    refreshGalleryJS();
                }
            });
    });
    $('button#btn_gallery_del').on('click', function() {
        $('#gallery-editable').block({ 
            message: '<h3>processing...</h3>', 
            css: { } 
        }); 
        Sijax.request('del_gallery',
            [ { active : getActiveGalleryNum() } ],
            {
                'complete': function() {
                    refreshGalleryJS();
                    $('#gallery-editable').unblock();
                }
            });
    });
    $('body').on('click', '.btn_gallery_del_img', function() {
        var $image_to_remove = $($($(this)[0]).parent().children()[0]);
        var url_to_remove = $image_to_remove.attr('src');
        $(this).remove();
        $image_to_remove.remove();
        refreshMasonry();
        Sijax.request('gallery_del_image', [{
            active : getActiveGalleryNum(),
            url : url_to_remove
        }],
            {
                'complete': function() {
                    refreshMasonry();
                }
            });
    });

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
          if (target.attr('class') == 'panel-heading')
            return false;

          var selection = window.getSelection(),
          range = selection.getRangeAt(0),
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
    });

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

    $('button#btn_desc_tbl_add').on('click', function() {
        Sijax.request('add_desc_table', [ {
            'desc_table'  : getDescriptionTable(),
            }], {'async': false});
        refreshDescriptionJS();
    });

    $('#btn_saveprofile').bind('click', function() {
        Sijax.request('save_profile', [
          {
            'header_title': br2nl($('#header_title').html()),
            'header_body' : br2nl($('#header_body').html()),
            'desc_table'  : getDescriptionTable(),
            'gallery_tabs': getGalleryTableTabs(),
          }
        ]);
        return false;
    });

    $('.posts').hide();
    Dropzone.autoDiscover = false;

    jQuery(window).load(function () {
        $('.posts').show();
        refreshMasonry();
    });
    $(window).bind('resize', function () {
        resizeMasonry();
    }).trigger('resize');

    refreshDescriptionJS();
    refreshGalleryJS();
    createAvatarDropZone('avatar-drop');
    createBkgDropZone('bkg-drop');
});
