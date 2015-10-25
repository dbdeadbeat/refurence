from flask import Blueprint, redirect, render_template, url_for, g, session, \
    get_template_attribute, current_app, request, make_response, jsonify
from werkzeug import secure_filename

from flask_application.controllers import TemplateView
from flask_application.profiles.decorators import ajax_catch_error
from flask_application.profiles.constants import profile_constants as pc
from flask_application.profiles.models import Profile, EditableImageTable, ImageLink, Path
from flask_application.utils.html import convert_html_entities, sanitize_html
from flask_application import app

from flask.ext.mobility.decorators import mobilized

import os.path
from copy import deepcopy
from random import randint
import urlparse
from PIL import Image
import StringIO


profiles = Blueprint('profiles', __name__)


def is_url(url):
    return urlparse.urlparse(url).scheme != ""


class ProfileView(TemplateView):
    def get(self, slug):
        profile = Profile.objects.get_or_404(username__iexact=slug)
        if current_app.dropbox.is_authenticated and\
           current_app.dropbox.account_info['email'] == profile.owner_email:
            return render_template('profiles/neo.html', profile=profile, is_me=True)
            #  return render_template('profiles/me.html', profile=profile)
        else:
            #  return render_template('profiles/detail.html', profile=profile)
            return render_template('profiles/neo.html', profile=profile)

    @mobilized(get)
    def get(self, slug):
        profile = Profile.objects.get_or_404(username=slug)
        return render_template('mobile/profiles/detail.html', profile=profile)


class ListView(TemplateView):
    def get(self, slug):
        if slug == 'all':
            return render_template('profiles/list.html', profiles=Profile.objects.all(), title='profiles')
        elif slug == 'examples':
            return render_template('profiles/list.html', profiles=Profile.objects(is_example=True), title='example profiles')
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
                                   title='example profiles')
        else:
            return redirect('404')


class EditView(ProfileView):
    def get(self, slug):
        profile = Profile.objects.get_or_404(username__iexact=slug)
        if current_app.dropbox.is_authenticated and \
           current_app.dropbox.account_info['email'] == profile.owner_email:
                session['temp_profile'] = deepcopy(profile)
                session['dropbox_paths_to_delete'] = []
                #  return render_template('profiles/edit.html', profile=profile)
                return render_template('profiles/neo_edit.html', profile=profile)
        else:
            return redirect('404')

    def get_user_profile_edit(self):
        if 'temp_profile' in session:

            if '_id' in session['temp_profile']:
                del session['temp_profile']['_id']

            return Profile(**session['temp_profile'])
        username = ''
        if current_app.dropbox.is_authenticated:
            username = current_app.dropbox.account_info['email']
        return Profile.objects.get_or_404(owner_email=username)

    def save_user_profile_edit(self, profile):
        if 'temp_profile' in session:
            session['temp_profile'] = profile
            return

        try:
            profile.save()
        except Exception as e:
            print 'faile', e

    # common html update functions
    def sidebar_html_update(self, obj_response, profile):
        sidebar_macro = get_template_attribute('profiles/_neo.html',
                                               'render_editable_imglinks')
        sidebar_html = sidebar_macro(profile.sidebar.img_links)
        obj_response.html("#imglink-container", sidebar_html)

        modal_macro = get_template_attribute('profiles/_neo.html', 'render_modals')
        modal_html = modal_macro(profile)
        obj_response.html("#modals", modal_html)

    def description_content_html_update(self, obj_response, profile):
        desc_macro = get_template_attribute('profiles/_neo.html', 'render_description_content')
        desc_html = desc_macro(profile.description)
        obj_response.html('#description-content', desc_html)

        desc_tabs_macro = get_template_attribute('profiles/_neo.html', 'render_description_tabs')
        desc_tabs_html = desc_tabs_macro(profile.description, True)
        obj_response.html('#left-sidebar-desc', desc_tabs_html)

    def gallery_html_update(self, obj_response, profile):
        navtabs_macro = get_template_attribute('profiles/_editable.html', 'render_navtabs_gallery')
        navtabs_html = navtabs_macro(profile.gallery)
        obj_response.html('#navtabs_gallery', navtabs_html)

        desc_macro = get_template_attribute('profiles/_editable.html', 'render_table_gallery')
        desc_html = desc_macro(profile.gallery)
        obj_response.html('#table_gallery', desc_html)

    def gallery_links_html_update(self, obj_response, profile, table):
        links_macro = get_template_attribute('profiles/_editable.html', 'render_gallery_table_links')
        links_html = links_macro(table)
        element = '#links' + str(table.order)
        obj_response.html(element, links_html)

    def extract_desc_content(self, tables):
        out = {}
        for tab_name, tbl in tables.iteritems():
            table = EditableImageTable()
            table.order = tbl['order']
            table.text = format_input(tbl['text'])
            out[tab_name] = table
        return out

    def update_description_content(self, obj_response, profile, tables):
        desc_images = [tbl.images for tbl in profile.description.get_tables()]
        profile.description.tables = self.extract_desc_content(tables)
        for k, tbl in profile.description.tables.iteritems():
            tbl.images = desc_images[tbl.order]

            size_limit = 4000
            if len(tbl.get_text()) > size_limit:
                obj_response.alert("ERROR: text must have < %d characters" % size_limit)
                return False

            if len(k) == 0:
                obj_response.alert("ERROR: notes cannot have empty titles")
                return False

        return True

    @ajax_catch_error
    def save_profile_handler(self, obj_response, content):
        profile = self.get_user_profile_edit()
        profile.header.title = format_input(content[pc['HEADER_TITLE']])
        profile.header.body = format_input(content[pc['HEADER_BODY']])

        if not self.update_description_content(obj_response, profile, content[pc['DESC_TABLE']]):
            return

        try:
            master_profile = Profile.objects.get(username=profile.username)
        except Exception as e:
            obj_response.alert('profile not found')
            obj_response.redirect(url_for('users.controlpanel'))
            return

        profile.id = master_profile.id
        try:
            profile.save()
        except Exception as e:
            print 'faile', e
            obj_response.alert('bad input, cannot save')
            return

        master_profile = Profile.objects.get(username=profile.username)
        if not profile.bkg_img and master_profile.bkg_img:
            master_profile.bkg_img = None
            master_profile.save()
        if not profile.bkg_color and master_profile.bkg_color:
            master_profile.bkg_color = None
            master_profile.save()

        for img in session['dropbox_paths_to_delete']:
            profile.dropbox_delete_file(img)
        del session['dropbox_paths_to_delete']
        profile.dropbox_cleanup()

        obj_response.redirect(url_for('profiles.detail',
                              slug=profile.username))

    @ajax_catch_error
    def discard_changes_handler(self, obj_response, content):
        username = current_app.dropbox.account_info['email']

        try:
            profile = Profile.objects.get_or_404(owner_email=username)
        except Exception:
            obj_response.alert('profile not found')
            obj_response.redirect(url_for('users.controlpanel'))
            return

        profile.dropbox_cleanup()
        obj_response.redirect(url_for('profiles.detail', slug=profile.username))

    def update_editable_text_handler(self, obj_response, content):
        profile = self.get_user_profile_edit()
        profile.header.title = format_input(content[pc['HEADER_TITLE']])
        profile.header.body = format_input(content[pc['HEADER_BODY']])

        if not self.update_description_content(obj_response, profile, content[pc['DESC_TABLE']]):
            return

        self.save_user_profile_edit(profile)

    def add_imglink_handler(self, obj_response, content):
        def get_default_imglink_img(idx):
            if (idx > 3):
                idx = randint(1, 3)
            if idx == 1:
                return url_for('static', filename='img/icon_email.png', _external=True)
            if idx == 2:
                return url_for('static', filename='img/icon_twitter.png', _external=True)
            return url_for('static', filename='img/icon_fa.png', _external=True)

        profile = self.get_user_profile_edit()

        if len(profile.sidebar.img_links) > 2:
            return

        imglink = ImageLink(img_url=get_default_imglink_img(len(profile.sidebar.img_links)), link_url='')
        profile.sidebar.img_links.append(imglink)
        self.save_user_profile_edit(profile)
        self.sidebar_html_update(obj_response, profile)

    def update_imglink_image_handler(self, obj_response, content):
        profile = self.get_user_profile_edit()

        idx = content['num']
        src = Path(private_path=content['files'][0]['path'])
        dst = profile.dropbox_get_non_gallery_image_directory().join(content['files'][0]['path'])

        if profile.sidebar.img_links[idx].dropbox_path:
            session['dropbox_paths_to_delete'].append(profile.sidebar.img_links[idx].dropbox_path)

        profile.sidebar.img_links[idx].dropbox_path = profile.dropbox_move_file(src, dst)
        profile.sidebar.img_links[idx].share()

        self.save_user_profile_edit(profile)
        self.sidebar_html_update(obj_response, profile)

    @ajax_catch_error
    def update_imglink_handler(self, obj_response, content):
        profile = self.get_user_profile_edit()

        if content['href'] and not is_url(content['href']):
            obj_response.alert('NOT A URL')
            return

        profile.sidebar.img_links[content['num']].link_url = content['href']

        self.save_user_profile_edit(profile)
        self.sidebar_html_update(obj_response, profile)

    @ajax_catch_error
    def del_imglink_handler(self, obj_response, content):
        profile = self.get_user_profile_edit()
        num = content['num']
        if len(profile.sidebar.img_links) > 0:
            del profile.sidebar.img_links[num]
        self.save_user_profile_edit(profile)
        self.sidebar_html_update(obj_response, profile)

    @ajax_catch_error
    def update_avatar_url_handler(self, obj_response, content):
        profile = self.get_user_profile_edit()

        new_file = content['files'][0]
        src = Path(private_path=new_file['path'])
        dst = profile.dropbox_get_non_gallery_image_directory().join(new_file['path'])

        if profile.header.avatar_dropbox_path:
            session['dropbox_paths_to_delete'].append(profile.header.avatar_dropbox_path)

        profile.header.avatar_dropbox_path = profile.dropbox_move_file(src, dst)
        profile.header.avatar_dropbox_path.share()

        self.save_user_profile_edit(profile)

        avtimg_macro = get_template_attribute('profiles/_neo.html', 'render_avatarimg')
        avt_html = avtimg_macro(profile.header)
        obj_response.html("#avatar", avt_html)

    @ajax_catch_error
    def add_desc_content_handler(self, obj_response, content):
        profile = self.get_user_profile_edit()
        num_tabls = len(profile.description.tables)

        if num_tabls >= 10:
            return

        attr_tabl = EditableImageTable()
        attr_tabl.text = 'write text here...'
        name = 'Note' + str(num_tabls)
        while name in profile.description.tables:
            num_tabls += 1
            name = 'Note' + str(num_tabls)
        attr_tabl.order = num_tabls

        if not self.update_description_content(obj_response, profile, content[pc['DESC_TABLE']]):
            return

        profile.description.add_table(name, attr_tabl)
        self.save_user_profile_edit(profile)
        self.description_content_html_update(obj_response, profile)

    @ajax_catch_error
    def del_desc_content_handler(self, obj_response, content):
        idx = int(content['num'])
        if idx < 0:
            return
        profile = self.get_user_profile_edit()

        if not self.update_description_content(obj_response, profile, content[pc['DESC_TABLE']]):
            return False

        profile.description.delete_table_by_order(idx)
        self.save_user_profile_edit(profile)
        self.description_content_html_update(obj_response, profile)

    @ajax_catch_error
    def change_color_handler(self, obj_response, content):
        profile = self.get_user_profile_edit()
        profile.colors[content['color']] = content['value']
        self.save_user_profile_edit(profile)

    @ajax_catch_error
    def change_font_handler(self, obj_response, content):
        profile = self.get_user_profile_edit()
        profile.fonts[content['font']] = content['value']
        self.save_user_profile_edit(profile)

    @ajax_catch_error
    def add_image_to_description_handler(self, obj_response, content):
        idx = int(content['num'])
        if idx < 0:
            return

        profile = self.get_user_profile_edit()
        table = profile.description.get_tables()[idx]

        if not table:
            return

        for idx, f in enumerate(table.images):
            session['dropbox_paths_to_delete'].append(f)
        table.images = []

        fdir = profile.dropbox_get_non_gallery_image_directory()
        for f in content['files']:
            src = Path(private_path=f['path'])
            dst = fdir.join(f['path'])
            table.images.append(profile.dropbox_move_file(src, dst))
        table.share()

        self.save_user_profile_edit(profile)
        self.description_content_html_update(obj_response, profile)

    def register_sijax(self):
        g.sijax.register_callback('save_profile', self.save_profile_handler)
        g.sijax.register_callback('discard_changes', self.discard_changes_handler)
        g.sijax.register_callback('update_editable_text', self.update_editable_text_handler)
        g.sijax.register_callback('add_imglink', self.add_imglink_handler)
        g.sijax.register_callback('update_imglink', self.update_imglink_handler)
        g.sijax.register_callback('update_imglink_image', self.update_imglink_image_handler)
        g.sijax.register_callback('del_imglink', self.del_imglink_handler)
        g.sijax.register_callback('add_desc_table', self.add_desc_content_handler)
        g.sijax.register_callback('del_desc_table', self.del_desc_content_handler)
        g.sijax.register_callback('update_avatar_url', self.update_avatar_url_handler)
        g.sijax.register_callback('change_color', self.change_color_handler)
        g.sijax.register_callback('change_font', self.change_font_handler)
        g.sijax.register_callback('add_image_to_description', self.add_image_to_description_handler)


def format_input(string):
    return convert_html_entities(sanitize_html(string))


# puts Profile constants into template rendering context
@profiles.context_processor
def inject_constants():
    return pc


# Register the urls
profiles.add_url_rule('/<slug>/', view_func=ProfileView.as_view('detail'))
profiles.add_url_rule('/<slug>/edit', view_func=EditView.as_view('edit'), methods=['GET', 'POST'])
profiles.add_url_rule('/site/profiles/<slug>', view_func=ListView.as_view('list'))


@app.route('/upload/', methods=('GET', 'POST'))
def upload():
    if not app.dropbox.is_authenticated:
        response = make_response('fail')
        response.mimetype = 'text/plain'
        return response

    if request.method == 'POST':
        data = dict((key, request.files.getlist(key)) for key in request.files.keys())

        out = []
        for k, f in data.iteritems():
            for file_obj in f:
                if file_obj:
                    client = app.dropbox.client
                    filename = secure_filename(file_obj.filename)
                    fname, ext = os.path.splitext(filename)
                    ext = ext[1:]

                    # allow gifs uncompressed cuz animated gifs are cool as hell
                    if ext == 'gif':
                        metadata = (client.put_file('/' + filename, file_obj.read(), overwrite=True))
                        metadata['dimensions'] = (0, 0)
                        out.append(metadata)
                        continue

                    img = Image.open(request.files[k])
                    wpercent = (1920 / float(img.size[0]))
                    hpercent = (1080 / float(img.size[1]))
                    if wpercent < 1.0:
                        hsize = int((float(img.size[1]) * float(wpercent)))
                        img = img.resize((1920, hsize), Image.ANTIALIAS)
                    elif hpercent < 1.0:
                        wsize = int((float(img.size[0]) * float(hpercent)))
                        img = img.resize((wsize, 1080), Image.ANTIALIAS)

                    filename = secure_filename(file_obj.filename)
                    fname, ext = os.path.splitext(filename)
                    ext = ext[1:]

                    if ext == 'png':
                        filename = fname + '.jpg'

                    # save all as jpg to make small as fuck files
                    ext = 'jpeg'

                    thumb_io = StringIO.StringIO()
                    img.save(thumb_io, ext.upper())
                    metadata = client.put_file('/' + filename, thumb_io.getvalue(), overwrite=True)
                    metadata['dimensions'] = (img.size[0], img.size[1])
                    out.append(metadata)

        return jsonify(**{'files': out})
