var js={};!function(n){n(document).on("click",".se-q",function(){var e=n(this).parents(".se-c"),s=e.find(".se-a"),e=e.find(".se-t");s.slideToggle(200),e.hasClass("se-o")?e.removeClass("se-o"):e.addClass("se-o")}),n(document).on("click","#top-page",function(){return n("html, body").animate({scrollTop:0},"slow"),!1}),n(document).on("click","#discoverclic",function(){n(this).addClass("hidde"),n("#closediscoverclic").removeClass("hidde"),n("#discover").addClass("show"),n("#requests").addClass("hidde"),n(".requests_menu").addClass("hidde"),n(".requests_menu_filter").removeClass("hidde")}),n(document).on("click","#closediscoverclic",function(){n(this).addClass("hidde"),n("#discoverclic").removeClass("hidde"),n("#discover").removeClass("show"),n("#requests").removeClass("hidde"),n(".requests_menu_filter").addClass("hidde"),n(".requests_menu").removeClass("hidde")}),n(document).on("click",".filtermenu a",function(){var e=n(this).attr("data-type");return n(".filtermenu a").removeClass("active"),n(this).addClass("active"),n("#type").val(e),!1}),n(document).on("click",".rmenu a",function(){var e=n(this).attr("data-tab");return n(".rmenu a").removeClass("active"),n(".tabox").removeClass("current"),n(this).addClass("active"),n("#"+e).addClass("current"),!1}),n(document).on("click",".clicklogin",function(){n(".login_box ").show()}),n(document).on("click","#c_loginbox",function(){n(".login_box ").hide()}),n(document).on("click",".nav-resp",function(){n("#arch-menu").toggleClass("sidblock"),n(".nav-resp").toggleClass("active")}),n(document).on("click",".nav-advc",function(){n("#advc-menu").toggleClass("advcblock"),n(".nav-advc").toggleClass("dactive")}),n(document).on("click",".report-video",function(){n("#report-video").toggleClass("report-video-active"),n(".report-video").toggleClass("report-video-dactive")}),n(document).on("click",".adduser",function(){n("#register_form").toggleClass("advcblock"),n(".form_fondo").toggleClass("advcblock"),n(".adduser").toggleClass("dellink")}),n(document).on("click",".search-resp",function(){n("#form-search-resp").toggleClass("formblock"),n(".search-resp").toggleClass("active")}),n(document).on("click",".wide",function(){n("#playex").toggleClass("fullplayer"),n(".sidebar").toggleClass("fullsidebar"),n(".icons-enlarge2").toggleClass("icons-shrink2")}),n(document).on("click",".sources",function(){n(".sourceslist").toggleClass("sourcesfix"),n(".listsormenu").toggleClass("icon-close2")}),n(document).keyup(function(e){27==e.keyCode&&(n(".login_box").hide(100),n("#result_edit_link").hide(100),n("#report-video").removeClass("report-video-active"),n("#moda-report-video-error").removeClass("show"),n("#moda-report-video-error").addClass("hidde"))}),n.each(["#tvload","#movload","#featload","#epiload","#seaload","#slallload","#sltvload","#slmovload",".genreload"],function(e,s){1<=n(s).length&&(n(".content").ready(function(){n(s).css("display","none")}),n(".content").load(function(){n(s).css("display","none")}))});for(var e=0,s=n(".items .item"),o=0;o<=s.length;o++)3<e?(n(".items .item:nth-child("+o+") .dtinfo").addClass("right"),dtAjax.classitem>e?e++:(e--,e--,e--,e--)):(n(".items .item:nth-child("+o+") .dtinfo").addClass("left"),e++);n.fn.exists=function(){return 0<e(this).length},js.model={events:{},extend:function(e){var o=n.extend({},this,e);return n.each(o.events,function(e,s){o._add_event(e,s)}),o},_add_event:function(e,s){var o=this,t=e,i="",a=document;0<e.indexOf(" ")&&(t=e.substr(0,e.indexOf(" ")),i=e.substr(e.indexOf(" ")+1)),"resize"!=t&&"scroll"!=t||(a=window),n(a).on(t,i,function(e){e.$el=n(this),"function"==typeof o.event&&(e=o.event(e)),o[s].apply(o,[e])})}},js.header=js.model.extend({$header:null,$sub_header:null,active:0,hover:0,show:0,y:0,opacity:1,direction:"down",events:{ready:"ready",scroll:"scroll","mouseenter #header":"mouseenter","mouseleave #header":"mouseleave"},ready:function(){this.$header=n("#header"),this.$sub_header=n("#sub-header"),this.active=1},mouseenter:function(){var e=n(window).scrollTop();this.hover=1,this.opacity=1,this.show=e,this.$header.stop().animate({opacity:1},250)},mouseleave:function(){this.hover=0},scroll:function(){var e,s,o,t;this.active&&(t=(s=(e=n(window).scrollTop())>=this.y?"down":"up")!==this.direction,this.y,o=this.$sub_header.outerHeight(),clearTimeout(this.t),e<70&&this.$header.removeClass("-white"),t&&(0==this.opacity&&"up"==s?(this.show=e)<o?this.show=0:this.show-=70:1==this.opacity&&"down"==s&&(this.show=e),this.show=Math.max(0,this.show)),this.$header.hasClass("-open")&&(this.show=e),this.hover&&(this.show=e),t=e-this.show,t=Math.max(0,t),t=(70-(t=Math.min(t,70)))/70,this.$header.css("opacity",t),o<e?this.$header.addClass("-white"):0==t&&this.$header.removeClass("-white"),this.y=e,this.direction=s,this.opacity=t)}})}(jQuery);

$(document).ready(function(){
	 
	$("body").on("click", "li:not(.active) [data-ajaxc]", function(){
		var $castom = $(this).attr("data-ajaxc"),
		    $cc = $(this).parent('li:not(.active)'),
			$targetBox = $(this).closest('.letter_home').children('.items_glossary');
		$targetBox.html('<div class="onloader"></div>');
		$.post(dle_root+"engine/ajax/custom.php", {castom:$castom}, function(data){
			$('.items_glossary').css('display','block');
			$targetBox.html('<div class="items animation-2">'+data+'</div>');
		});
		$cc.addClass('active').siblings().removeClass('active');
	});
	
	$(document).on('click', function(e) {
  if (!$(e.target).closest(".letter_home").length) {
    $('.items_glossary').hide();
	$('.items_glossary .animation-2').remove();
	$('.glossary li.active').removeClass('active');
  }
  e.stopPropagation();
});
});
(function () {

    document.addEventListener('submit', function(e) {

        var form = e.target;
        var storyInput = form.querySelector('input[name="story"], textarea[name="story"]');

        if (storyInput && storyInput.value.trim().length >= 4) {

            localStorage.setItem('last_dle_search_story', storyInput.value.trim());

            form.method = 'POST';
            form.action = '/index.php?do=search';

            var doInput = form.querySelector('input[name="do"]');
            if (!doInput) {
                doInput = document.createElement('input');
                doInput.type = 'hidden';
                doInput.name = 'do';
                form.appendChild(doInput);
            }
            doInput.value = 'search';

            var subInput = form.querySelector('input[name="subaction"]');
            if (!subInput) {
                subInput = document.createElement('input');
                subInput.type = 'hidden';
                subInput.name = 'subaction';
                form.appendChild(subInput);
            }
            subInput.value = 'search';

        }

    }, true);

})();

function list_submit(page) {

    page = parseInt(page) || 1;

    var story = '';

    var inp = document.querySelector('input[name="story"], textarea[name="story"]');

    if (inp && inp.value.trim()) {
        story = inp.value.trim();
    }

    if (!story) {
        story = localStorage.getItem('last_dle_search_story') || '';
    }

    if (!story || story.length < 4) {
        alert('Search word missing');
        return false;
    }

    var form = document.createElement('form');
    form.method = 'POST';
    form.action = '/index.php?do=search';

    var fields = {
        do: 'search',
        subaction: 'search',
        story: story,
        search_start: page
    };

    for (var key in fields) {
        var input = document.createElement('input');
        input.type = 'hidden';
        input.name = key;
        input.value = fields[key];
        form.appendChild(input);
    }

    document.body.appendChild(form);
    form.submit();

    return false;
}