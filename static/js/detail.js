$(function () {

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
            var gutter = parseInt($('.post').css('marginBottom'));
            var container = $('.posts');
            container.masonry({
                gutter: gutter,
                itemSelector: '.post',
                columnWidth: '.post'
            });
        });  
    }

    $(window).load(function () {
        $('.posts').show();
        refreshMasonry();
        $('#collapse0').collapse('show');
    });

    $(window).bind('resize', function () {
        resizeMasonry();
    }).trigger('resize');

    $('a[data-toggle="tab"]').each(function () {
        var $this = $(this);
        var $container = $('.posts');

        $this.on('shown.bs.tab', function () {
            $container.imagesLoaded( function () {
                refreshMasonry();
            });  
        });
    });

    $('.panel-body').on('click', function(event) {
        event = event || window.event;
        var target = event.target || event.srcElement,
        link = target.src ? target.parentNode : target,
        options = {index: link, event: event},
        links = [$(this).css('background-image').slice(4, -1)]
        console.log("LINK", options, links);
        blueimp.Gallery(links, options);
    })

    //document.getElementById('links').onclick = function (event) {
    $('.gallery-links').on('click', function (event) {
        event = event || window.event;
        var target = event.target || event.srcElement,
        link = target.src ? target.parentNode : target,
        options = {index: link, event: event},
        links = this.getElementsByTagName('a');
        blueimp.Gallery(links, options);
    });

    $('.collapse').collapse();
});
