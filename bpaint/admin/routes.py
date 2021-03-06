import os
import re

from flask import Blueprint, flash, redirect, render_template, request, url_for

from inspect import getmembers

from keyword import iskeyword

from PIL import Image, ImageFile

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from wtforms import IntegerField, SubmitField

from bpaint.admin.forms import ADD_ORIG_MEMBERS, AddToDatabaseForm, DeleteForm, UPDATE_ORIG_MEMBERS, UpdateDatabaseForm

bp = Blueprint('admin', __name__, static_folder='static', template_folder='templates', url_prefix='/admin')



def load_db(rec_id=None):
    from bpaint.models import Color
    records_all = Color.query.filter_by(id=rec_id).all() if rec_id else Color.query.all()
    records_all.sort(key=lambda r: r.name)
    return records_all

@bp.route('/')
def admin():
    return render_template('admin/index.html')

@bp.route('/db/')
def db_home():
    return render_template('admin/db_home.html')

@bp.route('/db/<string:operation>', methods=['GET', 'POST'])
@bp.route('/db/<string:operation>/<int:rec_id>', methods=['GET', 'POST'])
def db_add_update(*, operation=None, rec_id=None):
    records = load_db()
    form = None

    if operation == 'add':
        form_type = AddToDatabaseForm
        form_origs = ADD_ORIG_MEMBERS
        dest_get = 'admin/db_add.html'
        label = 'Add'
    elif operation == 'update':
        if not rec_id:
            choices = [{'id': record.id, 'name': record.name, 'swatch': record.swatch} for record in records]
            return render_template('admin/db_update_choices.html', choices=choices)
        else:
            form_type = UpdateDatabaseForm
            form_origs = UPDATE_ORIG_MEMBERS
            dest_get = 'admin/db_update.html'
            label = 'Update'
            del records[(rec_check := list(map(lambda r: r.id == rec_id, records))).index(True)]
    elif operation == 'delete':
            choices = [{'id': record.id, 'name': record.name, 'swatch': record.swatch} for record in records]
            return render_template('admin/db_delete_choices.html', choices=choices)
    else:
        flash('Error: Invalid Database Operation')
        return redirect(url_for('.db_home'))

    for member in getmembers(form_type):
        if member not in form_origs:
            if hasattr(form_type.__class__, member[0]):
                delattr(form_type.__class__, member[0])
            elif hasattr(form_type, member[0]):
                delattr(form_type, member[0])

    ingredients = []
    images = dict()
    current = None
    for record in records:
        ingredients.append((record.name, record.swatch))

    if form_type is AddToDatabaseForm and len(ingredients) < 2:
        ingredients = []
    else:
        if form_type is AddToDatabaseForm:  # len(ingredients) >= 2
            rec = None
            default = lambda _: 0
        else:  # form_type is UpdateDatabaseForm
            rec = load_db(rec_id)[0]
            rec_recipe = dict(zip(rec.ingredients, rec.quantities))
            default = lambda r: rec_recipe.get(r.id, 0)

        for record in records:
            setattr(form_type, f'color_{record.id}', IntegerField(record.name, default=default(record)))
            images[f'color_{record.id}'] = record.swatch
        setattr(form_type, 'submit2', SubmitField(f'{label} Color'))

        if rec:  # True only if form_type is UpdateDatabaseForm
            form = form_type(obj=rec.formdict)
            current = (rec.swatch, rec.name)

    if not form:
        form = form_type()

    if request.method == 'POST':
        if form.validate_on_submit():
            from bpaint import app, db, uploads
            from bpaint.models import Color, Recipe

            formdata = form.data

            db_entry = dict()
            color = Color.query.filter_by(id=rec_id).one() if rec_id else None

            formdata.pop('csrf_token')
            formdata.pop('visible_pure')
            formdata.pop('submit')
            formdata.pop('submit2', None)

            db_entry['name'] = formdata.pop('name')
            if rec:
                if db_entry['name'] != rec.name:
                    recipes = Recipe.query.filter(Recipe.ingredient_id == rec.id).all()
                    for recipe in recipes:
                        recipe.ingredient_name = db_entry['name']
                        db.session.add(recipe)

            db_entry['medium'] = formdata.pop('medium')
            db_entry['pure'] = formdata.pop('pure')
            if db_entry['pure']:
                db_entry['recipe'] = None
            else:
                db_entry['recipe'] = list(set([(color, quantity) for color in records for quantity in formdata.values() if formdata.get(f'color_{color.id}', -1) == quantity and quantity > 0]))
            if not db_entry['recipe']:
                del db_entry['recipe']

            if formdata.get('swatch'):
                image_file = formdata.pop('swatch')
                image_file.filename = secure_filename(image_file.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_file.filename)
                if form_type is AddToDatabaseForm and os.path.exists(image_path):
                    similar = [filename for filename in os.listdir(app.config['UPLOAD_FOLDER']) if (pattern := os.path.splitext(image_file.filename)[0]) in filename]
                    similar_map = map(lambda filename: re.match(pattern + '-(\d+)', filename), similar)
                    numbers = {int(m.group(1)) for m in similar_map if m}
                    for n in range(1, len(numbers) + 2):
                        if n in numbers:
                            continue
                        else:
                            image_file.filename = pattern + f'-{n}' + os.path.splitext(image_file.filename)[1]
                            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_file.filename)
                            break
                with open(image_path, 'w'):
                    image_file.save(image_path)
                ImageFile.LOAD_TRUNCATED_IMAGE = True
                with Image.open(image_path) as image:
                    image = image.resize((200, 200))
                    image.save(image_path)
                db_entry['swatch'] = url_for('static', filename=f'images/{image_file.filename}')
            elif color:  # no image provided for update
                db_entry['swatch'] = color.swatch
            else:  # no image provided for add
                flash('Must include an image.')
                return redirect(request.path)

            if rec_id:
                if db_entry['swatch'] != color.swatch:
                    old_image_name = color.swatch.rsplit('/', 1)[1]
                    old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], old_image_name)
                    os.remove(old_image_path)
                for k,v in db_entry.items():
                    setattr(color, k, v)

            if not color:
                color = Color(**db_entry)
            
            db.session.add_all([color, *color.recipe])
            db.session.commit()

            for attr in getmembers(form_type):
                if attr[0].startswith('color_'):
                    exec(f'del form.{attr[0]}')

            flash(f"{label} '{color.name}' Successful.")

            if rec_id:
                return redirect(url_for('.db_home') + 'update')
            return redirect(request.path)

        else:  # not form.validate_on_submit()
            flash(str(form.errors))
            return redirect(request.path)

    return render_template(dest_get, form=form, images=images, current=current)

@bp.route('/db/delete/<int:rec_id>', methods=['GET', 'POST'])
def db_delete_verify(rec_id, confirmed=False):
    from bpaint import app, db
    form = DeleteForm()

    if form.data['cancel']:
        flash('Delete Cancelled.')
        return redirect(url_for('.db_home'))

    rec = load_db(rec_id)[0]
    current = (rec.swatch, rec.name)
    affected = {r.name: r.swatch for r in rec.affects if r is not rec}
    confirmed = form.data['submit']

    if request.method == 'POST' and confirmed:
        image_names = [r.swatch.rsplit('/', 1)[1] for r in rec.affects]
        image_paths = [os.path.join(app.config['UPLOAD_FOLDER'], image_name) for image_name in image_names]
        for image_path in image_paths:
            os.remove(image_path)
        rec.delete()
        db.session.commit()

        flash(f'{rec.name} Successfully Deleted.')
        return redirect(url_for('.db_home'))

    return render_template('admin/db_delete_confirm.html', form=form, images={}, current=current, affected=affected)
