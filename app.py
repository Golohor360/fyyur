# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

from email.policy import default
import json
import logging
import dateutil.parser
import babel
from flask import (
    Flask,
    render_template,
    request,
    Response,
    flash,
    redirect,
    url_for,
    jsonify,
    abort
)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from pytz_deprecation_shim import timezone
from forms import *
from flask_migrate import Migrate
import sys
from models import (
    app,
    db,
    Venue,
    Artist,
    Show
)

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route('/')
def index():
    recent_artists = Artist.query.order_by(Artist.id.desc()).limit(10).all()
    venues = Venue.query.order_by(Venue.id.desc()).limit(10).all()
    # to get only requeried data
    unique_venues = Venue.query.distinct(Venue.city, Venue.state).all()
    data = []
    # to store current time
    for unique_venue in unique_venues:
        # to store venues in each city
        venue_data = []
        for venue in venues:
            if unique_venue.city == venue.city:
                venue_data.append({
                    'id': venue.id,
                    'name': venue.name
                })
        data.append({
            'city': unique_venue.city,
            'state': unique_venue.state,
            'venues': venue_data
        })
    print(data)
    return render_template('pages/home.html', recent_artists=recent_artists,
                           areas=data)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # num_upcoming_shows should be aggregated based on number
    # of upcoming shows per venue.
    data = []
    error = False
    try:
        error = False
        # get all venues form the database
        venues = Venue.query.all()
        # to get only requeried data
        unique_venues = Venue.query.distinct(Venue.city, Venue.state).all()
        # to store the current time
        current_time = datetime.now()
        # to store current time
        for unique_venue in unique_venues:
            # to store venues in each city
            venue_data = []
            for venue in venues:
                if unique_venue.city == venue.city:
                    venue_data.append({
                        'id': venue.id,
                        'name': venue.name,
                        'num_upcoming_shows': Show.query.filter(db.and_(
                            Show.start_time > current_time, Show.venue_id
                            == venue.id)
                        ).count()
                    })
            data.append({
                'city': unique_venue.city,
                'state': unique_venue.state,
                'venues': venue_data
            })
    except Exception:
        error = True
        print(sys.exc_info())
        abort(500)
    finally:
        # to check if there was any errors
        if error:
            flash(
                u'Due to an error from our end. We are unable to\
                show you the venues page', 'alert-danger')
            return render_template('pages/venues.html', areas=data)
        else:
            return render_template('pages/venues.html', areas=data)


@ app.route('/venues/search', methods=['POST'])
def search_venues():
    # search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop"
    # and "Park Square Live Music & Coffee"
    data = []
    search_term = request.form['search_term']
    # to query the db base on the search value from the form
    results = Venue.query.with_entities(Venue.id, Venue.name).filter(
        Venue.name.ilike("%" + search_term + "%"))
    venues = results.all()
    for venue in venues:
        data.append({
            'id': venue.id,
            'name': venue.name,
            'num_upcoming_shows': Show.query.filter(db.and_(
                Show.start_time > datetime.now(), Show.venue_id
                == venue.id
            )).count()
        })
    response = {
        "count": results.count(),
        "data": data
    }
    return render_template('pages/search_venues.html',
                           results=response, search_term=request.form.
                           get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # to get specific venue
    venue = Venue.query.get(venue_id)
    # to get current time
    current_date = datetime.now()
    # to get shows for specific venue
    venue_shows = Show.query.filter(Show.venue_id == venue_id)
    # to store past shows
    p_shows = []
    # to store upcoming shows
    u_shows = []
    # loop through all the venue shows
    for show in venue_shows:
        if show.start_time < current_date:
            # appending past shows
            p_shows.append({
                'artist_id': show.id,
                'artist_name': show.artist.name,
                'artist_image_link': show.venue.image_link,
                'start_time': format_datetime(str(show.start_time))
            })
        else:
            u_shows.append({
                'artist_id': show.id,
                'artist_name': show.artist.name,
                'artist_image_link': show.venue.image_link,
                'start_time': format_datetime(str(show.start_time))
            })
    # appending the details to the data var.
    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": p_shows,
        "upcoming_shows": u_shows,
        "past_shows_count": len(p_shows),
        "upcoming_shows_count": len(u_shows),
    }
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    error = False
    form = VenueForm()
    # form validation
    if form.validate_on_submit():
        try:
            error = False
            new_record = Venue(
                name=form.data['name'],
                city=form.data['city'],
                state=form.data['state'],
                address=form.data['address'],
                phone=form.data['phone'],
                image_link=form.data['image_link'],
                facebook_link=form.data['facebook_link'],
                seeking_talent=form.data['seeking_talent'],
                seeking_description=form.data['seeking_description'],
                website=form.data['website_link'],
                genres=form.data['genres']
            )
            db.session.add(new_record)
            db.session.commit()
            print('working')
        except Exception:
            error: True
            db.session.rollback()
            print(sys.exc_info())
        finally:
            db.session.close()
            if error:
                flash(u'An error occurred. Venue ' +
                      form.data['name'] + ' could not be listed.',
                      'alert-danger')
                # return to the artist edit page with an error
                return render_template('forms/new_venue.html', form=form)
            else:
                # # on successful db insert, flash success
                flash(u'Venue ' + form.data['name'] +
                      ' was successfully listed!', 'alert-info')
                return render_template('pages/home.html')
    else:
        flash(u'An error occurred. Venue ' +
              form.data['name'] + ' could not be listed.', 'alert-danger')
        # ## Additional feature ## #
        # to show the user only the first error
        for error_messages in form.errors.items():
            for index in range(len(error_messages)):
                if index == 0:
                    flash(u'' + str(error_messages), 'alert-danger')
        # return to the artist edit page with an error
        return render_template('forms/new_venue.html', form=form)


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # SQLAlchemy ORM to delete a record. Handle cases where the
    # session commit could fail.
    error = False
    try:
        error = False
        Show.query.filter_by(venue_id=venue_id).delete()
        Venue.query.filter_by(id=venue_id).delete()
        db.session.commit()
    except Exception:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if not error:
            # BONUS CHALLENGE: Implement a button to delete a
            # Venue on a Venue Page, have it so that
            # clicking that button delete it from the db then
            # redirect the user to the homepage
            flash(u'Venue was successfully deleted!', 'alert-info')
            return render_template('pages/home.html')


#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    # the database
    # to get all artist from the database
    data = []
    artists = Artist.query.all()
    for artist in artists:
        data.append({
            "id": artist.id,
            "name": artist.name
        })
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado",
    # and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    # to get the search from the search form
    data = []
    search_term = request.form['search_term']
    # to query the db base on the search value from the form
    results = Artist.query.with_entities(Artist.id, Artist.name).filter(
        Artist.name.ilike("%" + search_term + "%"))
    artists = results.all()
    for artist in artists:
        data.append({
            'id': artist.id,
            'name': artist.name,
            'num_upcoming_shows': Show.query.filter(db.and_(
                Show.start_time > datetime.now(), Show.artist_id
                == artist.id
            )).count()
        })
    response = {
        "count": results.count(),
        "data": data
    }
    return render_template('pages/search_artists.html',
                           results=response, search_term=request.form.
                           get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # table, using artist_id

    # to get specific artist for the datase
    artist = Artist.query.get(artist_id)

    # get the current time
    current_date = datetime.now()

    # to get shows for specific artist
    artist_shows = Show.query.filter(Show.artist_id == artist_id)

    # to store past shows
    p_shows = []

    # to store upcoming shows
    u_shows = []

    # loop through all the artist shows
    for show in artist_shows:
        if show.start_time < current_date:
            # appending past shows
            p_shows.append({
                'venue_id': show.id,
                'venue_name': show.venue.name,
                'venue_image_link': show.venue.image_link,
                'start_time': format_datetime(str(show.start_time))
            })
        else:
            u_shows.append({
                'venue_id': show.id,
                'venue_name': show.venue.name,
                'venue_image_link': show.venue.image_link,
                'start_time': format_datetime(str(show.start_time))
            })

    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": p_shows,
        "upcoming_shows": u_shows,
        "past_shows_count": len(p_shows),
        "upcoming_shows_count": len(u_shows),
    }

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    return render_template('forms/edit_artist.html',
                           form=form, artist=artist)

#
# to get list of artist genres for the artist edit page


@app.route('/get_artist_genres/<int:artist_id>', methods=['POST'])
def get_artist_genres(artist_id):
    error = False
    data = {}
    try:
        error = False
        artist_genres = Artist.query.with_entities(
            Artist.genres).filter_by(id=artist_id).first()
        data['artist_genres'] = artist_genres[0]
    except Exception:
        error = True
        print(sys.exc_info())
    finally:
        if error:
            abort(500)
        else:
            return jsonify(data)


#
# to get list of venue genres for the venue edit page


@app.route('/get_venue_genres/<int:venue_id>', methods=['POST'])
def get_venue_genres(venue_id):
    error = False
    data = {}
    try:
        error = False
        venue_genres = Venue.query.with_entities(
            Venue.genres).filter_by(id=venue_id).first()
        data['venue_genres'] = venue_genres[0]
        print(data)
    except Exception:
        error = True
        print(sys.exc_info())
    finally:
        if error:
            abort(500)
        else:
            return jsonify(data)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # artist record with ID <artist_id> using the new attributes
    error = True
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    # form validation
    if form.validate_on_submit():
        try:
            error = False
            # populationg the artist form
            form.populate_obj(artist)
            # committing the update to the db
            db.session.commit()
        except Exception:
            error = True
            db.session.rollback()
            print(sys.exc_info())
        finally:
            db.session.close()
            if error:
                # an error instead.
                flash(u'An error occurred. Artist ' +
                      form.data['name'] + ' could not be edited.\
                        ', 'alert-danger')
                # return to the artist edit page with an error
                return redirect(url_for('edit_artist', artist_id=artist_id))
            else:
                # # on successful db insert, flash success
                flash(u'Artist ' + form.data['name'] +
                      ' was successfully edited!', 'alert-info')
                # return to the artist edit page with an error
                return redirect(url_for('show_artist', artist_id=artist_id))
    else:
        # return form validation error
        flash(u'An error occurred. Artist ' +
              form.data['name'] + ' could not be edited.', 'alert-danger')
        # ## Additional feature ## #
        # to show the user only the first error
        for error_messages in form.errors.items():
            for index in range(len(error_messages)):
                if index == 0:
                    flash(u'' + str(error_messages), 'alert-danger')
        # return to the artist edit page with an error
        return redirect(url_for('edit_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # venue record with ID <venue_id> using the new attributes
    error = False
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    # form validation
    if form.validate_on_submit():
        try:
            error = False
            # populating the venue form
            form.populate_obj(venue)
            # committing the update to the db
            db.session.commit()
        except Exception:
            error = True
            db.session.rollback()
            print(sys.exc_info())
        finally:
            db.session.close()
            if error:
                # return form validation error
                flash(u'An error occurred. Venue ' +
                      form.data['name'] + ' could not be edited.',
                      'alert-danger')
                # return to the venue edit page with an error
                return redirect(url_for('edit_venue', venue_id=venue_id))
            else:
                # # on successful db insert, flash success
                flash(u'Venue ' + form.data['name'] +
                      ' was successfully edited!', 'alert-info')
                return redirect(url_for('show_venue', venue_id=venue_id))

    else:
        # return form validation error
        flash(u'An error occurred. Venue ' +
              form.data['name'] + ' could not be edited.', 'alert-danger')
        # ## Additional feature ## #
        # to show the user only the first error
        for error_messages in form.errors.items():
            for index in range(len(error_messages)):
                if index == 0:
                    flash(u'' + str(error_messages), 'alert-danger')
        # return to the venue edit page with an error
        return redirect(url_for('edit_venue', venue_id=venue_id))
    # return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    error = False
    form = ArtistForm()
    # form validation
    if form.validate_on_submit():
        try:
            error = False
            new_record = Artist(
                name=form.data['name'],
                city=form.data['city'],
                state=form.data['state'],
                phone=form.data['phone'],
                website=form.data['website_link'],
                facebook_link=form.data['facebook_link'],
                seeking_venue=form.data['seeking_venue'],
                seeking_description=form.data['seeking_description'],
                image_link=form.data['image_link'],
                genres=form.data['genres']
            )
            db.session.add(new_record)
            db.session.commit()
        except Exception:
            error = True
            db.session.rollback()
            print(sys.exc_info())
        finally:
            db.session.close()
            if error:
                flash(u'An error occurred. Artist ' +
                      form.data['name'] + ' could not be listed.',
                      'alert-danger')
                return render_template('forms/new_artist.html', form=form)
            else:
                # # on successful db insert, flash success
                flash(u'Artist ' + form.data['name'] +
                      ' was successfully listed!', 'alert-info')
                return render_template('pages/home.html')

    else:
        flash(u'An error occurred. Artist ' +
              form.data['name'] + ' could not be listed.', 'alert-danger')
        # ## Additional feature ## #
        # to show the user only the first error
        for error_messages in form.errors.items():
            for index in range(len(error_messages)):
                if index == 0:
                    print(error_messages)
                    flash(u'' + str(error_messages), 'alert-danger')
        return render_template('forms/new_artist.html', form=form)


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # to get all shows from the datebase
    data = []
    shows = Show.query.all()
    for show in shows:
        data.append({
            "venue_id": show.venue.id,
            "venue_name": show.venue.name,
            "artist_id": show.artist.id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": str(show.start_time)
        })
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db,
    # upon submitting new show listing form
    # record in the db, instead
    error = False
    form = ShowForm()
    # form validation
    if form.validate_on_submit():
        try:
            error = False
            # new record to be inserted
            new_record = Show(artist_id=form.data['artist_id'],
                              venue_id=form.data['venue_id'],
                              start_time=form.data['start_time'])
            db.session.add(new_record)
            db.session.commit()
        except Exception:
            error = True
            db.session.rollback()
            print(sys.exc_info())
        finally:
            db.session.close()
            if error:
                flash(u'An error occurred. Show could not be listed.',
                      'alert-danger')
                return redirect(url_for('create_shows'))
            else:
                # on successful db insert, flash success
                flash(u'Show was successfully listed!', 'alert-info')
                return render_template('pages/home.html')
    else:
        # return user to the create page with error message
        # e.g., flash('An error occurred. Show could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
        flash(u'An error occurred. Show could not be listed.', 'alert-danger')
        return redirect(url_for('create_shows'))


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s\
             [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
