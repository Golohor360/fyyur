from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.dialects.postgresql import ARRAY


app = Flask(__name__)
db = SQLAlchemy()
migrate = Migrate(app, db)


# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500), nullable=False)
    facebook_link = db.Column(db.String(120), nullable=False)
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String)
    genres = db.Column(ARRAY(db.String(120)), nullable=False, default=[])
    website = db.Column(db.String)
    shows = db.relationship('Show', backref='venue',
                            lazy='joined', cascade='all, delete')

    def __repr__(self):
        return f'<Venue id: {self.id}, name: {self.name}, city: {self.city},\
        state: {self.state}, address: {self.address}, phone: {self.phone}\
        image_link: {self.image_link}, facebook_link: {self.facebook_link},\
        seeking_talent: {self.seeking_talent}, seeking_description: \
        {self.seeking_description}, genres: {self.genres}, website: \
        {self.website}, shows: {self.shows}>'


class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column(ARRAY(db.String(120)), nullable=False, default=[])
    image_link = db.Column(db.String(500), nullable=False)
    facebook_link = db.Column(db.String(120), nullable=False)
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String)
    website = db.Column(db.String)
    shows = db.relationship('Show', backref='artist',
                            lazy='joined', cascade='all, delete')

    def __repr__(self):
        return f'<Artist id: {self.id}, name: {self.name}, city: {self.city},\
        state: {self.state}, phone: {self.phone}, genres: {self.genres}\
        image_link: {self.image_link}, facebook_link: {self.facebook_link},\
        seeking_venue: {self.seeking_venue}, seeking_description:\
        {self.seeking_description}, website: {self.website}, shows:\
        {self.shows}>'


class Show(db.Model):
    __tablename__ = 'show'

    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey(
        'venue.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey(
        'artist.id'), nullable=False)
    start_time = db.Column('start_time', db.DateTime, nullable=False)

    def __repr__(self):
        return f'<Show venue_id: {self.venue_id}, artist_id: {self.artist_id},\
        start_time: {self.start_time}>'
