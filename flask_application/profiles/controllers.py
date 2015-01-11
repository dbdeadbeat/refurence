from flask import Blueprint, request, redirect, render_template, url_for, g, session, jsonify, get_template_attribute
from flask.views import MethodView
import flask_sijax

from flask_application.controllers import TemplateView
from flask_application.profiles.constants import profile_constants as pc
from flask_application.profiles.models import *
from flask.ext.security.core import current_user, AnonymousUser

from flask_application.utils.html import convert_html_entities, sanitize_html

from flask.ext.mobility.decorators import mobilized

from copy import deepcopy
from random import randint


profiles = Blueprint('profiles', __name__)

class ProfileView(TemplateView):
    def get(self, slug):
        profile = Profile.objects.get_or_404(username__iexact=slug)
        if current_user.is_authenticated() and current_user.username == slug:
            return render_template('profiles/me.html', profile=profile)
        else:
            return render_template('profiles/detail.html', profile=profile)

    @mobilized(get)
    def get(self, slug):
        profile = Profile.objects.get_or_404(username=slug)
        return render_template('mobile/profiles/detail.html', profile=profile)

class ListView(TemplateView):
    def get(self, slug):
        if slug == 'all':
          return render_template('profiles/list.html',
              profiles=Profile.objects.all(),
              title='profiles')
        elif slug == 'examples':
          return render_template('profiles/list.html',
              profiles=Profile.objects(is_example=True),
              title = 'example profiles')
        else:
          return redirect('404')

    @mobilized(get)
    def get(self, slug):
        if slug == 'all':
          return render_template('mobile/profiles/list.html',
              profiles=Profile.objects.all(),
              title='profiles')
        elif slug == 'examples':
          return render_template('mobile/profiles/list.html',
              profiles=Profile.objects(is_example=True),
              title = 'example profiles')
        else:
          return redirect('404')

class EditView(ProfileView):
    def get(self, slug):
        if current_user.is_authenticated() and current_user.username == slug:
            profile = Profile.objects.get_or_404(username__iexact=current_user.username)
            session['temp_profile'] = deepcopy(profile)
            return render_template('profiles/edit.html', profile=profile) 
        else:
            return redirect('404')

    def get_user_profile_edit(self):
        if 'temp_profile' in session:
          return Profile(**session['temp_profile'])
        return Profile.objects.get_or_404(username=current_user.username)

    def save_user_profile_edit(self, profile):
        if 'temp_profile' in session:
          session['temp_profile'] = profile
          return

        try:
          profile.save()
        except Exception as e:
          print 'faile'

    # common html update functions
    def sidebar_html_update(self, obj_response, profile):
        sidebar_macro = get_template_attribute('profiles/_editable.html', 'render_editablesidebar')
        sidebar_html = sidebar_macro(profile.sidebar)
        obj_response.html("#sidebar", sidebar_html)

    def desc_table_html_update(self, obj_response, profile):
        navtabs_desc_macro = get_template_attribute('profiles/_editable.html', 'render_navtabs_description')
        navtabs_desc_html = navtabs_desc_macro(profile.description)
        obj_response.html('#navtabs_description', navtabs_desc_html)

        desc_macro = get_template_attribute('profiles/_editable.html', 'render_table_description')
        desc_html = desc_macro(profile.description)
        obj_response.html('#table_description', desc_html)

    def gallery_html_update(self, obj_response, profile):
        navtabs_desc_macro = get_template_attribute('profiles/_editable.html', 'render_navtabs_gallery')
        navtabs_desc_html = navtabs_desc_macro(profile.gallery)
        obj_response.html('#navtabs_gallery', navtabs_desc_html)

        desc_macro = get_template_attribute('profiles/_editable.html', 'render_table_gallery')
        desc_html = desc_macro(profile.gallery)
        obj_response.html('#table_gallery', desc_html)

    def gallery_links_html_update(self,  obj_response, profile, active):
        links_macro = get_template_attribute('profiles/_editable.html', 'render_gallery_table_links')
        links_html = links_macro(profile.gallery.tables[active])
        element = '#links' + str(profile.gallery.get_keys().index(active))
        obj_response.html(element, links_html)


    # ajax request callbacks
    def discard_changes_handler(self, obj_response, content):
        # profile = Profile.objects.get_or_404(username=current_user.username)
        # profile_html = render_template('profiles/edit.html', profile=profile) 
        pass

    def save_profile_handler(self, obj_response, content):
        profile                    = self.get_user_profile_edit()
        profile.header.title       = format_input(content[pc['HEADER_TITLE']])
        profile.header.body        = format_input(content[pc['HEADER_BODY']])
        profile.notes.title        = format_input(content[pc['NOTES_TITLE']])
        profile.notes.body         = format_input(content[pc['NOTES_BODY']])
        profile.description.title  = format_input(content[pc['DESC_HEADER']])
        profile.description.tables = extract_tables(content[pc['DESC_TABLE']])
        profile.gallery.title      = format_input(content[pc['GALLERY_TITLE']])

        tabs = [format_input(x) for x in content[pc['GALLERY_TABS']]]
        keys = profile.gallery.get_keys()
        for idx in range(0, len(keys)):
          profile.gallery.tables[tabs[idx]] = profile.gallery.tables.pop(keys[idx])

        master_profile = Profile.objects.get(username=current_user.username)
        profile.id = master_profile.id
        try:
            profile.save()
        except Exception as e:
            obj_response.alert('bad input, cannot save')
            return

        master_profile = Profile.objects.get(username=current_user.username)
        if not profile.bkg_img:
            master_profile.bkg_img = None
            master_profile.save()

        obj_response.redirect(url_for('profiles.detail', slug=current_user.username))

    def add_imglink_handler(self, obj_response, content):

        def get_default_imglink_img(idx):
          if (idx > 3):
            idx = randint(1,3)
          if idx == 1:
            return url_for('static', filename='img/icon_email.png', _external=True)
          if idx == 2:
            return url_for('static', filename='img/icon_twitter.png', _external=True)
          return url_for('static', filename='img/icon_fa.png', _external=True)

        profile = self.get_user_profile_edit()

        if len(profile.sidebar.img_links) > 8:
            return

        imglink = ImageLink(
                img_url=get_default_imglink_img(len(profile.sidebar.img_links)),
                link_url='')
        profile.sidebar.img_links.append(imglink)
        self.save_user_profile_edit(profile)
        self.sidebar_html_update(obj_response, profile)

    def update_imglink_handler(self, obj_response, content):
        num = content['num']
        imgurl = content['imgurl']
        href = content['href']

        if not imgurl and not href:
            return

        profile = self.get_user_profile_edit()
        if href:
            profile.sidebar.img_links[content['num']].link_url = href
        if imgurl:
            profile.sidebar.img_links[content['num']].img_url = imgurl

        self.save_user_profile_edit(profile)
        self.sidebar_html_update(obj_response, profile)

    def del_imglink_handler(self, obj_response, content):
        profile = self.get_user_profile_edit()
        num = content['num']
        if len(profile.sidebar.img_links) > 0:
            del profile.sidebar.img_links[num]
        self.save_user_profile_edit(profile)
        self.sidebar_html_update(obj_response, profile)

    def update_avatar_url_handler(self, obj_response, avatar_url):
        profile = self.get_user_profile_edit()

        profile.header.avatar_url = avatar_url if avatar_url else None
        self.save_user_profile_edit(profile)
        avtimg_macro = get_template_attribute('profiles/_editable.html', 'render_avatarimg')
        avt_html = avtimg_macro(profile.header)
        obj_response.html("#avatar", avt_html)

    def add_desc_table_handler(self, obj_response, content):
        profile = self.get_user_profile_edit()
        num_tabls = len(profile.description.tables)

        if num_tabls >= 10:
            return

        profile.description.tables = extract_tables(content[pc['DESC_TABLE']])

        attr_tabl = EditableTable()
        attr_tabl.rows.append(EditableRow(cells=['text here']))
        attr_tabl.order = num_tabls
        profile.description.tables['Attributes' + str(num_tabls)] = attr_tabl
        self.save_user_profile_edit(profile)
        self.desc_table_html_update(obj_response, profile)

    def del_desc_table_handler(self, obj_response, content):
        profile = self.get_user_profile_edit()
        profile.description.tables = extract_tables(content[pc['DESC_TABLE']])
        profile.description.delete_table(content['active'])
        self.save_user_profile_edit(profile)
        self.desc_table_html_update(obj_response, profile)

    def add_gallery_handler(self, obj_response, content):

        profile = self.get_user_profile_edit()
        num_gallerys = len(profile.gallery.tables) + 1
        if num_gallerys >= 10:
            return

        imgtable = ImageTable()
        imgtable.order = num_gallerys
        profile.gallery.tables['Images'+str(num_gallerys)] = imgtable
        self.save_user_profile_edit(profile)
        self.gallery_html_update(obj_response, profile)

    def del_gallery_handler(self, obj_response, content):
        profile = self.get_user_profile_edit()
        profile.gallery.delete_table(content['active'])
        self.save_user_profile_edit(profile)
        self.gallery_html_update(obj_response, profile)

    def gallery_add_image_handler(self, obj_response, content):
        profile = self.get_user_profile_edit()
        profile.gallery.tables[content['active']].img_urls.append(content['url'])
        self.save_user_profile_edit(profile)

        self.gallery_links_html_update(obj_response, profile, content['active'])

    def gallery_del_image_handler(self, obj_response, content):
        profile = self.get_user_profile_edit()
        if content['url'] in profile.gallery.tables[content['active']].img_urls:
            profile.gallery.tables[content['active']].img_urls.remove(content['url'])
        self.save_user_profile_edit(profile)

        self.gallery_links_html_update(obj_response, profile, content['active'])

    def gallery_add_directory_handler(self, obj_response, content):
        profile = self.get_user_profile_edit()
        profile.gallery.tables[content['active']].img_dir = content['url'] if content['url'] else None
        self.save_user_profile_edit(profile)

        self.gallery_links_html_update(obj_response, profile, content['active'])

    def change_bkg_handler(self, obj_response, content):
        profile = self.get_user_profile_edit()
        profile.bkg_img = content['url'] if content['url'] else None
        if not profile.bkg_img:
            profile.bkg_color = content['color'] if content['color'] else None
        self.save_user_profile_edit(profile)
        if profile.bkg_img:
            element = 'url(' + profile.bkg_img + ') no-repeat center center fixed'
        else:
            element = profile.bkg_color
        obj_response.css('body', 'background', element)
        obj_response.css('body', 'background-size', 'cover')

    def change_color_handler(self, obj_response, content):
        profile = self.get_user_profile_edit()
        profile.colors[content['color']] = content['value']
        self.save_user_profile_edit(profile)

    def change_font_handler(self, obj_response, content):
        profile = self.get_user_profile_edit()
        profile.fonts[content['font']] = content['value']
        self.save_user_profile_edit(profile)

    def register_sijax(self):
        g.sijax.register_callback('save_profile', self.save_profile_handler)
        g.sijax.register_callback('discard_changes', self.discard_changes_handler)
        g.sijax.register_callback('add_imglink', self.add_imglink_handler)
        g.sijax.register_callback('update_imglink', self.update_imglink_handler)
        g.sijax.register_callback('del_imglink', self.del_imglink_handler)
        g.sijax.register_callback('add_desc_table', self.add_desc_table_handler)
        g.sijax.register_callback('del_desc_table', self.del_desc_table_handler)
        g.sijax.register_callback('add_gallery', self.add_gallery_handler)
        g.sijax.register_callback('del_gallery', self.del_gallery_handler)
        g.sijax.register_callback('gallery_add_image', self.gallery_add_image_handler)
        g.sijax.register_callback('gallery_del_image', self.gallery_del_image_handler)
        g.sijax.register_callback('gallery_add_directory', self.gallery_add_directory_handler)
        g.sijax.register_callback('update_avatar_url', self.update_avatar_url_handler)
        g.sijax.register_callback('change_bkg', self.change_bkg_handler)
        g.sijax.register_callback('change_color', self.change_color_handler)
        g.sijax.register_callback('change_font', self.change_font_handler)

# puts Profile constants into template rendering context
@profiles.context_processor
def inject_constants():
    return pc

# utility functions
def extract_tables(desc_table):
    tables = {}
    for tab_name,tbl in desc_table.iteritems():
        table = EditableTable();
        table.order = tbl['order']
        for r in tbl['rows']:
            table.rows.append(EditableRow(cells=r))
        tables[tab_name] = table
    return tables

def format_input(string):
    return convert_html_entities(sanitize_html(string))

# Register the urls
profiles.add_url_rule('/<slug>/', view_func=ProfileView.as_view('detail'))
profiles.add_url_rule('/<slug>/edit', view_func=EditView.as_view('edit'), methods=['GET', 'POST'])
profiles.add_url_rule('/site/profiles/<slug>', view_func=ListView.as_view('list'))
