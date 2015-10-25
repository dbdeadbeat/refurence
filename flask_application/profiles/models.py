from flask import url_for, current_app
from flask_application.models import db, FlaskDocument
from flask_application.profiles.constants import profile_constants as pc

from flask_application.utils.imagehosting import get_hosted_image_urls, get_hosted_dir_urls

from flask_application import app

import copy
import itertools
import os
import random
import StringIO
import glob
from PIL import Image


class Path(db.EmbeddedDocument):
    private_path = db.StringField(required=True)
    public_path = db.StringField()
    is_dir = db.BooleanField(default=False)
    public_urls = db.ListField(db.StringField(default=''))

    # TODO make shared
    def get_all_files_as_urls(self):
        # return self.public_urls
        if self.public_path:
            if os.path.splitext(self.public_path)[1]:
                return [self.public_path + '?raw=1']
            else:
                return get_hosted_image_urls(self.public_path)
        return []

    def get_all_files_as_media(self):
        dropbox_paths = Path._get_all_dropbox_paths(self.private_path)
        return [app.dropbox.client.media(p['path'])['url'] for p in dropbox_paths]

    def get_all_files_as_paths(self):
        dropbox_paths = Path._get_all_dropbox_paths(self.private_path)
        return [Path(private_path=p['path'], is_dir=p['is_dir']) for p in dropbox_paths]

    def join(self, path):
        return Path(private_path=self.private_path + '/' + path)

    def basename(self):
        return self.private_path.split('/')[-1]

    def share(self):
        self.public_path = str(app.dropbox.client.share(self.private_path, short_url=False)['url'])
        if '?' in self.public_path:
            self.public_path = self.public_path[0:self.public_path.index('?')]
        self.public_urls = []

    @staticmethod
    def _get_all_dropbox_paths(path):
        out = []
        dropbox_files = app.dropbox.client.metadata(path)
        if dropbox_files['is_dir']:
            for c in dropbox_files['contents']:
                out.append(c)
        else:
            out.append(dropbox_files)
        return out


class ImageLink(db.EmbeddedDocument):
    img_url = db.StringField(required=True)
    link_url = db.StringField(default='#')
    dropbox_path = db.EmbeddedDocumentField('Path')

    def get_image_url(self):
        if app.dropbox.is_authenticated:
            if self.dropbox_path:
                url = self.dropbox_path.get_all_files_as_media()
                if len(url) > 0:
                    return url[0]
        return self.img_url

    def share(self):
        if not self.dropbox_path:
            return
        self.dropbox_path.share()
        urls = self.dropbox_path.get_all_files_as_urls()
        if len(urls) < 1:
            return
        self.img_url = urls[0]


class EditableImageTable(db.EmbeddedDocument):
    images = db.ListField(db.EmbeddedDocumentField('Path'))
    order = db.IntField(min_value=0, max_value=10)
    text = db.StringField()

    def get_image_links(self):
        return list(itertools.chain(*[img_path.get_all_files_as_urls() for img_path in self.images]))

    def share(self):
        map(lambda x: x.share(), self.images)

    def get_text(self):
        return self.text


class ImageTable(db.EmbeddedDocument):
    image_urls = db.ListField(db.StringField())
    order = db.IntField(default=0, min_value=0, max_value=10)
    name = db.StringField(default="Images")
    dropbox_path = db.EmbeddedDocumentField('Path')

    def is_removeable(self, img_url):
        return True

    def get_image_urls(self, debug=False):
        if debug:
            out = []
            for i in range(0, 10):
                x = random.choice([200, 150, 100, 300])
                y = random.choice([200, 150, 100, 300])
                out.append('http://placehold.it/' + str(x) + 'x' + str(y))
            return out
        else:
            if app.dropbox.is_authenticated:
                return self.dropbox_path.get_all_files_as_media()
            else:
                return get_hosted_image_urls(self.dropbox_path.public_path)
            return self.dropbox_path.get_all_files_as_urls()

    def get_image_paths(self):
        return self.dropbox_path.get_all_files_as_paths()

    def share(self):
        # self.image_urls = []
        # for p in self.get_image_paths():
            # p.share()
            # self.image_urls += p.get_all_files_as_urls()
        self.dropbox_path.share()

    def get_image_style(self, url):
        width = 200
        height = 200
        return 'max-width:' + str(width) + 'px; max-height:' + str(height) + 'px;'


class StylableContent(db.EmbeddedDocument):
    meta = {
        'allow_inheritance': True,
    }

    def is_renderable(self):
        return True


class SideBarContent(StylableContent):
    img_links = db.ListField(db.EmbeddedDocumentField('ImageLink'))


class HeaderContent(StylableContent):
    title = db.StringField(required=True, max_length=256, default='blarg!!')
    body = db.StringField(max_length=16384, default="Add Text Here!")
    avatar_url = db.URLField(max_length=16384)
    avatar_dropbox_path = db.EmbeddedDocumentField('Path')

    def get_avatar_url(self):
        if self.avatar_dropbox_path:
            url = self.avatar_dropbox_path.get_all_files_as_urls()
            if len(url) > 0:
                return url[0]
        self.avatar_dropbox_path = None
        return self.avatar_url


class NotesContent(StylableContent):
    title = db.StringField(max_length=128, default='Important Notes')
    body = db.StringField(max_length=16384)

    def is_renderable(self):
        if self.title or self.body:
            return True
        return False


class TabbedContent(StylableContent):
    def get_keys(self):
        return sorted(self.tables.keys(), key=lambda x: self.tables[x].order)

    def get_tables(self):
        return sorted(self.tables.values(), key=lambda x: x.order)

    def get_table_by_name(self, name):
        if name in self.tables:
            return self.tables[name]

    def add_table(self, name, table):
        self.tables[name] = table

    def delete_table(self, name):
        keys = self.get_keys()
        order_counter = 0
        for k in keys:
            if k == name:
                del self.tables[k]
            else:
                order_counter += 1
                self.tables[k].order = order_counter

    def delete_table_by_order(self, idx):
        keys = self.get_keys()
        order_counter = 0
        for k in keys:
            if order_counter == idx:
                del self.tables[k]
            else:
                self.tables[k].order = order_counter
            order_counter += 1

    def is_renderable(self):
        values = self.tables.values()
        if len(values) <= 0:
            return False
        return True


class DescriptionContent(TabbedContent):
    title = db.StringField(max_length=128, default='Description')
    tables = db.MapField(db.EmbeddedDocumentField('EditableImageTable'))

    def share(self):
        map(lambda x: x.share(), self.images)


class GalleryContent(TabbedContent):
    title = db.StringField(max_length=128, default='Gallery')
    tables = db.ListField(db.EmbeddedDocumentField('ImageTable'))

    def get_table_names(self):
        return [tbl.name for tbl in self.tables]

    def get_tables(self):
        return self.tables

    def is_renderable(self):
        return len(self.tables)


class Profile(FlaskDocument):
    meta = {
        'allow_inheritance': True,
        'indexes': ['username'],
    }

    owner_email = db.StringField()
    username = db.StringField(required=True)
    bkg_img = db.URLField(max_length=16384)
    bkg_color = db.StringField(max_length=256, default=None)
    is_example = db.BooleanField(default=False)
    is_default = db.BooleanField(default=False)

    sidebar = db.EmbeddedDocumentField('SideBarContent', default=SideBarContent())
    header = db.EmbeddedDocumentField('HeaderContent', default=HeaderContent())
    notes = db.EmbeddedDocumentField('NotesContent', default=NotesContent())
    description = db.EmbeddedDocumentField('DescriptionContent', default=DescriptionContent())
    gallery = db.EmbeddedDocumentField('GalleryContent', default=GalleryContent())
    colors = db.MapField(db.StringField(max_length=32),
                         default={
                             pc['COLOR_MAIN']: 'rgba(68,68,78,0.85)',
                             pc['COLOR_INNER']: 'rgba(48,48,68,1.0)',
                             pc['COLOR_HEADERS']: 'lightblue',
                             pc['COLOR_LINKS']: '#2a6496',
                             pc['COLOR_TEXT']: 'cadetblue',
                             pc['COLOR_TABS']: '#34495e'})
    fonts = db.MapField(db.StringField(max_length=256),
                        default={
                            pc['FONT_HEADERS']: '',
                            pc['FONT_LINKS']: '',
                            pc['FONT_TEXT']: ''})
    dropbox_profile_images_dirname = '_profile_images_DO_NOT_MODIFY'
    bkg_dropbox_path = db.EmbeddedDocumentField('Path')
    dropbox_root_public_path = db.StringField()

    def save(self, *args, **kwargs):
        super(Profile, self).save(*args, **kwargs)

    def delete(self):
        app.dropbox.client.file_delete(self.dropbox_root().private_path)
        super(Profile, self).delete()

    def dropbox_root(self):
        refurence_name = 'refurence_' + self.username
        paths = Path(private_path='/').get_all_files_as_paths()
        fdir = None
        for p in paths:
            path_name = p.private_path[1:len(p.private_path)]
            if path_name == refurence_name:
                return p
        if not fdir:
            return Path(private_path=app.dropbox.client.file_create_folder(refurence_name)['path'])

    def dropbox_cleanup(self):
        #  self._dropbox_delete_root_files()
        #  self._dropbox_delete_unused_folders()
        self._dropbox_delete_unused_images()

    def dropbox_create_folder(self, path):
        root_path = self.dropbox_root()
        root_path.share()
        self.dropbox_root_public_path = root_path.public_path
        paths = root_path.get_all_files_as_paths()
        for p in paths:
            if p.basename() == path and p.is_dir:
                return Path(private_path=p.private_path)

        new_dir = app.dropbox.client.file_create_folder(root_path.join(path).private_path)
        return Path(private_path=new_dir['path'])

    def dropbox_delete_file(self, path):
        try:
            app.dropbox.client.file_delete(path.private_path)
        except Exception:
            return

    def dropbox_get_non_gallery_image_directory(self):
        folder_path = self.dropbox_create_folder(Profile.dropbox_profile_images_dirname)
        return Path(private_path=folder_path.private_path)

    def dropbox_move_file(self, src, dst):
        new_path = ''
        try:
            new_path = app.dropbox.client.file_move(src.private_path, dst.private_path)['path']
        except Exception as e:
            if e.status == 403:
                self.dropbox_delete_file(dst)
                new_path = app.dropbox.client.file_move(src.private_path, dst.private_path)['path']

        return Path(private_path=new_path)

    def get_background_url(self):
        if self.bkg_dropbox_path:
            bkg_url = self.bkg_dropbox_path.get_all_files_as_urls()
            if len(bkg_url) > 0:
                return bkg_url[0]

        if self.bkg_img:
            return self.bkg_img
        return None

    def get_galleries(self):
        class MonkeyPatchTable():
            def __init__(self, data):
                self.data = data

            def get_image_urls(self, debug=False):
                return self.data

            def get_image_style(self, url):
                width = 128
                height = 128
                return 'max-width:' + str(width) + 'px; max-height:' + str(height) + 'px;'

        class MonkeyPatchGallery():
            def __init__(self, data):
                self.data = data

            def get_table_names(self):
                return [self.data['name']]

            def get_tables(self):
                return [MonkeyPatchTable(self.data['imgs'])]

            def is_renderable(self):
                return True

        dropbox_paths = get_hosted_dir_urls(self.dropbox_root_public_path)
        out = []
        for p in dropbox_paths:
            if p['name'] == Profile.dropbox_profile_images_dirname:
                continue
            p['imgs'] = get_hosted_image_urls(p['url'])
            out.append(MonkeyPatchGallery(p))
        return out

    def get_gallery_names(self):
        dropbox_paths = get_hosted_dir_urls(self.dropbox_root_public_path)
        out = []
        for p in dropbox_paths:
            if p['name'] == Profile.dropbox_profile_images_dirname:
                continue
            out.append(p['name'])
        return out

    def _dropbox_delete_root_files(self):
        paths = Path(private_path='/').get_all_files_as_paths()
        for p in paths:
            if not p.is_dir:
                self.dropbox_delete_file(p.private_path)

    def _dropbox_delete_unused_folders(self):
        files = self.dropbox_root().get_all_files_as_paths()
        gallery_names = self.gallery.get_table_names()
        for f in files:
            if f.is_dir and f.basename() not in gallery_names and \
               f.basename() != Profile.dropbox_profile_images_dirname:
                self.dropbox_delete_file(f)

    def _dropbox_delete_unused_images(self):
        files_in_dropbox = self.dropbox_get_non_gallery_image_directory().get_all_files_as_paths()

        paths_used_in_description = [x.images for x in self.description.get_tables()]
        paths_used_in_profile = [p.private_path for p in list(itertools.chain(*paths_used_in_description))]
        if self.header.avatar_dropbox_path:
            paths_used_in_profile.append(self.header.avatar_dropbox_path.private_path)
        if self.bkg_dropbox_path:
            paths_used_in_profile.append(self.bkg_dropbox_path.private_path)

        for imglink in self.sidebar.img_links:
            if imglink.dropbox_path:
                paths_used_in_profile.append(imglink.dropbox_path.private_path)

        paths_to_delete = filter(lambda x: x.private_path not in paths_used_in_profile, files_in_dropbox)
        map(self.dropbox_delete_file, paths_to_delete)

    @staticmethod
    def initialize_to_default(profile):
        if not app.dropbox.is_authenticated:
            return None

        default_profile = Profile.objects(is_default=True)
        if not default_profile:
            default_profile = Profile.create_default_profile()
        else:
            default_profile = default_profile[0]

        self_uname = profile.username
        self_id = profile.id

        profile = copy.deepcopy(default_profile)

        profile.id = self_id
        profile.username = self_uname
        profile.is_default = False
        profile.header.title = profile.username + " refurence"
        profile.header.body = "name: " + profile.username +\
            "\nspecies: animal\n\npress the 'Edit' button to create your refurence!!\n"

        profile.header.avatar_url = url_for('static', filename='img/avatar.png', _external=True)

        example_files = glob.glob('static/img/examples/*')
        for table in profile.gallery.get_tables():
            table.dropbox_path = profile.dropbox_create_folder(table.name)

            for filename in example_files:
                fname, ext = os.path.splitext(filename)
                basename = os.path.basename(filename)
                ext = ext[1:]
                if ext == 'jpg':
                    ext = 'jpeg'

                client = app.dropbox.client
                img = Image.open(filename)
                thumb_io = StringIO.StringIO()
                img.save(thumb_io, 'JPEG')
                upload_path = '/' + basename
                client.put_file(upload_path, thumb_io.getvalue(), overwrite=True)
                profile.dropbox_move_file(Path(private_path=upload_path), table.dropbox_path.join(upload_path))

        return profile

    @staticmethod
    def create_default_profile():
        profile = Profile(username='vX9P6zy9SARJCzvR2gJtQw27')
        profile.is_default = True
        profile.bkg_img = url_for('static', filename='img/bkg.jpg', _external=True)

        profile.header.title = profile.username + " refurence"
        profile.header.body = "name: " + profile.username +\
            "\nspecies: animal\n\npress the 'Edit' button to create your refurence!!\n"

        profile.header.avatar_url = url_for('static', filename='img/avatar.png', _external=True)

        profile.notes.title = "Important Notes"
        profile.notes.body = \
            "Add important notes, details, info, and other stuff for the artist to see here\n\
            * please send an email to me@me.com\n\
            * the best color reference is the 'color_reference.png' file in the gallery\n\
            * etc.."

        count = 0
        attr_tabl = EditableImageTable()
        attr_tabl.order = count
        count+=1
        attr_tabl.text = """
this section here in the center of the page, with the image on the left and textbox on the right, is a NOTE\n
these are intended to be used for showing off one specific image that you want to write a note to the artist about\n
example:\n
- IMAGE = a head shot of your character
- TITLE = best haircut
- TEXT = this is the best rendering of my character's hair, please use this as the main reference for the hair style\n 
you can add more notes when Editing, by pressing '+' next to Notes in the sidebar
        """
        profile.description.tables['Tutorial: Notes'] = attr_tabl

        attr_tabl = EditableImageTable()
        attr_tabl.order = count
        count+=1
        attr_tabl.text = """
Links are in the sidebar\n
you can assign them a url, this is useful for linking an artist to your FA, Email, or Twitter account\n
you can add a LINK when Editing, by pressing '+' next to Links in the sidebar\n
        """
        profile.description.tables['Tutorial: Links'] = attr_tabl

        attr_tabl = EditableImageTable()
        attr_tabl.order = count
        count+=1
        attr_tabl.text = """
Galleries are the images displayed below\n
each gallery corresponds to a folder in you Dropbox for this refurence\n
add a new gallery by creating a folder in you Dropbox for this refurence, ie under "Apps -> refurence -> refurence_?"\n
upload images to this folder, refresh the page, and you will see them displayed in a new gallery\n
for more information, click the '?' button next to Galleries in the sidebar while Editing\n
        """
        profile.description.tables['Tutorial: Galleries'] = attr_tabl

        img_tabl = ImageTable()
        img_tabl.img_dir = ''
        img_tabl.image_urls = []
        img_tabl.name = 'Reference Images'
        profile.gallery.tables.append(img_tabl)

        profile.fonts[pc['FONT_HEADERS']] = 'Jura'

        profile.save()

        return profile

    @staticmethod
    def is_name_taken(name):
        try:
            p = Profile.objects.get(username=name)
            if p:
                return True
            return False
        except Exception:
            return False

    @staticmethod
    def is_name_valid(name):
        for rule in current_app.url_map.iter_rules():
            str_rule = str(rule)
            str_rule = str_rule[1:len(str_rule)]
            if str_rule.startswith(name):
                return False
        if Profile.is_name_taken(name):
            return False
        return True
