from flask import url_for, current_app
from flask_application.models import db, FlaskDocument
from flask_application.profiles.constants import profile_constants as pc
from flask_application.utils.imagehosting import get_hosted_image_urls

from flask_application import app

import copy

class ImageLink(db.EmbeddedDocument):
    img_url = db.URLField(required=True)
    link_url = db.StringField()

class EditableRow(db.EmbeddedDocument):
    cells = db.ListField(db.StringField(max_length=1024))

class EditableTable(db.EmbeddedDocument):
    meta = {
        'allow_inheritance': True,
    }

    rows = db.ListField(db.EmbeddedDocumentField('EditableRow'))
    order = db.IntField(min_value=0, max_value=10)

    def get_text(self):
        out = ''
        for r in self.rows:
            for c in r.cells:
                out += c
        return out

class EditableImageTable(EditableTable):
    images = db.ListField(db.StringField())

    def get_image_links(self):
        out = []
        for idx, img in enumerate(self.images):
            try:
                out.append(app.dropbox.client.media(img)['url'])
            except Exception:
                self.images[idx] = ''
                out.append('')
                continue
        return out

class ImageTable(db.EmbeddedDocument):
    img_dir = db.StringField()
    img_urls = db.ListField(db.StringField())
    order = db.IntField(default=0, min_value=0, max_value=10)
    name = db.StringField(default="Images")
    dropbox_path = db.StringField()

    def is_removeable(self, img_url):
        if img_url in self.img_urls:
            return True
        return False

    def get_hosted_images(self):
        if not self.img_dir:
            return []
        return get_hosted_image_urls(self.img_dir)

    def get_image_urls(self):
        out = self.get_hosted_images()
        try:
            dropbox_files = app.dropbox.client.metadata(self.dropbox_path)
            for c in dropbox_files['contents']:
                out.append(app.dropbox.client.media(c['path'])['url'])
        except Exception:
            pass
        return out

class StylableContent(db.EmbeddedDocument):
    meta = {
    'allow_inheritance': True,
    }

    def is_renderable(self):
        return True

class SideBarContent(StylableContent):
    img_links = db.ListField(db.EmbeddedDocumentField('ImageLink'))

class HeaderContent(StylableContent):
    title      = db.StringField(required=True, max_length=256, default='blarg!!')
    body       = db.StringField(max_length=16384, default="Add Text Here!")
    avatar_url = db.URLField(max_length=16384)

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
    owner_email = db.StringField()
    username    = db.StringField(required=True)
    bkg_img     = db.URLField(max_length=16384)
    bkg_color   = db.StringField(max_length=256)
    is_example  = db.BooleanField(default=False)
    is_default  = db.BooleanField(default=False)

    sidebar     = db.EmbeddedDocumentField('SideBarContent', default=SideBarContent())
    header      = db.EmbeddedDocumentField('HeaderContent', default=HeaderContent())
    notes       = db.EmbeddedDocumentField('NotesContent', default=NotesContent())
    description = db.EmbeddedDocumentField('DescriptionContent', default=DescriptionContent())
    gallery     = db.EmbeddedDocumentField('GalleryContent', default=GalleryContent())
    colors      = db.MapField(db.StringField(max_length=32), default= {
                                            pc['COLOR_MAIN'] : 'rgba(68,68,78,0.85)',
                                            pc['COLOR_INNER'] : 'rgba(48,48,68,1.0)',
                                            pc['COLOR_HEADERS'] :  'lightblue',
                                            pc['COLOR_LINKS'] :    '#2a6496',
                                            pc['COLOR_TEXT'] :     'cadetblue',
                                            pc['COLOR_TABS'] :     '#34495e'
                                            });
    fonts       = db.MapField(db.StringField(max_length=256), default= {
                                            pc['FONT_HEADERS'] :     '',
                                            pc['FONT_LINKS'] :     '',
                                            pc['FONT_TEXT'] :     '',
                                            });
    dropbox_profile_images_dirname = '_profile_images'

    def delete(self):
        app.dropbox.client.file_delete(self.dropbox_root())
        super(Profile, self).delete()

    def dropbox_root(self):
        files = app.dropbox.client.metadata('/')['contents']
        fdir = None
        for f in files:
            path_name = f['path'][1:len(f['path'])]
            if path_name == self.username:
                return f['path']
        if not fdir:
            return app.dropbox.client.file_create_folder(self.username)['path']

    def dropbox_cleanup(self):
        self._dropbox_delete_unused_folders()
        self._dropbox_delete_root_files()

    def dropbox_create_folder(self, path):
        fdir = self.dropbox_root()
        files = app.dropbox.client.metadata(fdir)['contents']
        for f in files:
            path_name = f['path'].split('/')[-1]
            if path_name == path and f['is_dir']:
                return f['path']
        return app.dropbox.client.file_create_folder(fdir+'/'+path)['path']

    def dropbox_delete_file(self, path):
        try:
            app.dropbox.client.file_delete(path)
        except Exception:
            return

    def dropbox_get_non_gallery_image_directory(self):
        return self.dropbox_create_folder(Profile.dropbox_profile_images_dirname)

    def dropbox_move_file(self, src, dst):
        try:
            return app.dropbox.client.file_move(src, dst)
            # table.img_urls.append(md['path'])
        except Exception as e:
            if e.status == 403:
                app.dropbox.client.file_delete(dst)
                return app.dropbox.client.file_move(src, dst)

    def get_absolute_url(self):
        return url_for('profile', kwargs={"slug": self.username})

    def _dropbox_delete_root_files(self):
        files = app.dropbox.client.metadata('/')['contents']
        for f in files:
            print 'FILE', f
            if not f['is_dir']:
                app.dropbox.client.file_delete(f['path'])

    def _dropbox_delete_unused_folders(self):
        root = self.dropbox_root()
        files = app.dropbox.client.metadata(root)['contents']
        gallery_names = self.gallery.get_table_names()
        for f in files:
            if f['is_dir']:
                path_name = f['path'].split('/')[-1]
                if path_name not in gallery_names and \
                        path_name != Profile.dropbox_profile_images_dirname:
                    app.dropbox.client.file_delete(f['path'])

    def __unicode__(self):
        return self.username

    meta = {
        'allow_inheritance': True,
        'indexes': ['username'],
    }

    @staticmethod
    def initialize_to_default(profile):
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
            "\nspecies: animal\n\npress the 'Edit Profile' to create your refurence!!\n"

        for table in profile.gallery.get_tables():
            table.dropbox_path = profile.dropbox_create_folder(table.name)

        return profile


    @staticmethod
    def create_default_profile():
        profile = Profile(username='vX9P6zy9SARJCzvR2gJtQw27')
        profile.is_default = True
        profile.bkg_img = url_for('static', filename='img/bkg.jpg', _external=True)

        profile.header.title = profile.username + " refurence"
        profile.header.body = "name: " + profile.username +\
            "\nspecies: animal\n\npress the 'Edit Profile' to create your refurence!!\n"

        profile.header.avatar_url = url_for('static', filename='img/avatar.png', _external=True)

        profile.notes.title = "Important Notes"
        profile.notes.body = \
        "Add important notes, details, info, and other stuff for the artist to see here\n\
        * please send an email to me@me.com\n\
        * the best color reference is the 'color_reference.png' file in the gallery\n\
        * etc.."

        count = 0
        attr_tabl = EditableImageTable()
        attr_rows = [
                EditableRow(cells=[
                    'add/delete a tab',
                    'press the "+/-" icons to add a new tab'
                    ]),
                EditableRow(cells=[
                    'add an image',
                    'press the "image" button, paste a url into the dialog, and click submit'
                    ]),
                EditableRow(cells=[
                    'delete an image',
                    'press the "image" button, paste a url into the dialog, and click submit'
                    ]),
                EditableRow(cells=[
                    'add a synced GoogleDrive/Dropbox folder',
                    'press the "folder" button, paste a url into the dialog, and click submit',
                    'all images in the directory will be synced'
                    ]),
                EditableRow(cells=[
                    'delete a synced GoogleDrive/Dropbox folder',
                    'press the "folder" button, leave the dialog blank, and click submit',
                    ]),
                ]
        attr_tabl.rows += attr_rows
        attr_tabl.order = count; count+=1
        profile.description.tables['Editing Galleries'] = attr_tabl

        attr_tabl = EditableImageTable()
        attr_rows = [
                EditableRow(cells=[
                    'add/delete an imagelink',
                    'click the "+/-" buttons in the sidebar'
                    ]),
                EditableRow(cells=[
                    'change a imagelink image',
                    'click the imagelnk, paste a url into the image dialog, and click submit'
                    ]),
                EditableRow(cells=[
                    'change a imagelink link',
                    'click the imagelnk, paste a url into the link dialog, and click submit'
                    ]),
                ]
        attr_tabl.rows += attr_rows
        attr_tabl.order = count; count+=1
        profile.description.tables['Editing ImageLinks'] = attr_tabl

        attr_tabl = EditableImageTable()
        attr_rows = [
                EditableRow(cells=[
                    'change background',
                    'click Edit Style - Change Background, paste a url, click submit'
                    ]),
                EditableRow(cells=[
                    'change colors',
                    'click Edit Style - Change Colors, select colors, click choose'
                    ]),
                EditableRow(cells=[
                    'change fonts',
                    'click Edit Style - Change Font, select font'
                    ]),
                ]
        attr_tabl.rows += attr_rows
        attr_tabl.order = count; count+=1
        profile.description.tables['Editing Background/Colors/Fonts'] = attr_tabl

        img_tabl = ImageTable()
        img_tabl.img_dir = ''
        img_tabl.img_urls = []
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
        except Exception as e:
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
