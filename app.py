#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *

from datetime import datetime
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# TODO: connect to a local postgresql database
# --> Done. Please check details in config.py

from flask_migrate import Migrate
migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    # done. added columns: genres, website_link, seeking_talent, seeking_description, and relations: shows
    genres = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(120))
    shows = db.relationship('Show', backref='venue', lazy=True)
    
    def __repr__(self):
        return "<Venue %s Name %s>" %(self.id, self.name)

class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    # done. added columns: website_link, seeking_venue, seeking_description, and relations: shows
    website_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(120))
    shows = db.relationship('Show', backref='artist', lazy=True)
    
    def __repr__(self):
        return "<Artist %s Name %s>" %(self.id, self.name)

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
# done. Check details in each model class


class Show(db.Model):
    __tablename__ = 'shows'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.now(), nullable=False)

    def __repr__(self):
        return "<Show %s Artist %s Venue %s time %s>" %(self.id, self.artist_id, self.venue_id, self.start_time)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#
from babel.dates import format_datetime

def format_datetime(value, format='medium'):
  # instead of just date = dateutil.parser.parse(value)
  # added if/else to handeled a datetime input
  if isinstance(value, str):
      date = dateutil.parser.parse(value)
  else:
      date = value
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  # find all city/state
  cityState = db.session.query(Venue.city, Venue.state).distinct(Venue.city, Venue.state)
  ans = []  
  for cs in cityState:
      venue_info = Venue.query.filter_by(state = cs.state).filter_by(city = cs.city).all()
      venue_detail = []
      for ven in venue_info:
          venue_detail.append({'id': ven.id, 
                               'name': ven.name, 
                               'num_upcoming_shows': len( db.session.query(Show).filter(Show.start_time > datetime.now(), Show.venue_id == ven.id).all() )})
      ans.append( {'city': cs.city, 'state': cs.state, 'venues': venue_detail} )   
     
  return render_template('pages/venues.html', areas=ans);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  response = {}
  search_term = request.form.get('search_term', '')
  venues = Venue.query.filter(Venue.name.ilike("%" + search_term + "%")).all()
  data = []
  for venue in venues:
      data.append( {"id": venue.id, 
                    'name': venue.name, 
                    'num_upcoming_shows':  len( db.session.query(Show).filter(Show.start_time > datetime.now(), Show.venue_id == venue.id).all() )} )
  response['count'] = len(data)
  response['data'] = data
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  # done.
  venue = Venue.query.get(venue_id)
  genres = venue.genres.replace('{', '').replace('}', '').split(',')
  data = {"id": venue.id,
         "name": venue.name,
         "genres": genres,
         "address": venue.address,
         "city": venue.city,
         "state": venue.state,
         "phone": venue.phone,
         "website": venue.website_link,
         "facebook_link": venue.facebook_link,
         "seeking_talent": venue.seeking_talent,
         "seeking_description": venue.seeking_description,
         "image_link": venue.image_link,
         "past_shows": [],
         "upcoming_shows": [],
         "past_shows_count": 0,
         "upcoming_shows_count": 0,
   }
  # past shows
  past_shows_list = []
  past_shows_db = Show.query.filter(Show.start_time < datetime.now(), Show.venue_id == venue_id).all()
  for show in past_shows_db:
      artist = Artist.query.get(show.artist_id)
      past_shows_list.append( {'artist_id': show.artist_id, 'artist_name': artist.name, 'artist_image_link': artist.image_link ,'start_time': show.start_time} )
  # future shows
  future_shows_list = []
  future_shows_db = Show.query.filter(Show.start_time >= datetime.now(), Show.venue_id == venue_id).all()
  for show in future_shows_db:
      artist = Artist.query.get(show.artist_id)
      future_shows_list.append( {'artist_id': show.artist_id, 'artist_name': artist.name, 'artist_image_link': artist.image_link ,'start_time': show.start_time} )      
  data['past_shows'] = past_shows_list
  data['upcoming_shows'] = future_shows_list
  data['past_shows_count'] = len(past_shows_list)
  data['upcoming_shows_count'] = len(future_shows_list)
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  # done.
  try:      
    venue = Venue(name = request.form['name'],
                  city = request.form['city'],
                  state = request.form['state'],
                  address = request.form['address'],
                  phone = request.form['phone'],
                  image_link = request.form['image_link'],
                  facebook_link = request.form['facebook_link'],
                  genres = request.form.getlist('genres'),
                  website_link = request.form['website_link'],
                  seeking_talent = request.form.get('seeking_talent') == 'y',
                  seeking_description = request.form['seeking_description'] )
    db.session.add(venue)
    db.session.commit()          
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  # done.
  try:
      Venue.query.filter_by(id=venue_id).delete()
      db.session.commit()
  except:
      db.session.rollback()
  finally:
      db.session.close()

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  # please check show_venue.html for details
  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  # done.
  data = Artist.query.all()
  artists = []
  for art in data:
      artists.append( {'id': art.id, 'name': art.name} )
  return render_template('pages/artists.html', artists=artists)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  # done.
  response = {}
  search_term = request.form.get('search_term', '')
  artists = Artist.query.filter(Artist.name.ilike("%" + search_term + "%")).all()
  data = []
  for artist in artists:
      data.append( {"id": artist.id, 
                    'name': artist.name, 
                    'num_upcoming_shows':  len( db.session.query(Show).filter(Show.start_time > datetime.now(), Show.artist_id == artist.id).all() )} )
  response['count'] = len(data)
  response['data'] = data
  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  # done.
  data = {}  
  artist = Artist.query.get(artist_id)
  genres = artist.genres.replace('{', '').replace('}', '').split(',')
  data = {"id": artist.id,
         "name": artist.name,
         "genres": genres,
         "city": artist.city,
         "state": artist.state,
         "phone": artist.phone,
         "website": artist.website_link,
         "facebook_link": artist.facebook_link,
         "seeking_venue": artist.seeking_venue,
         "seeking_description": artist.seeking_description,
         "image_link": artist.image_link,
         "past_shows": [],
         "upcoming_shows": [],
         "past_shows_count": 0,
         "upcoming_shows_count": 0,
   }
  
  # past shows
  past_shows_list = []
  past_shows_db = Show.query.filter(Show.start_time < datetime.now(), Show.artist_id == artist_id).all()
  for show in past_shows_db:
      venue = Venue.query.get(show.venue_id)
      past_shows_list.append( {'venue_id': show.venue_id, 'venue_name': venue.name, 'venue_image_link': venue.image_link ,'start_time': show.start_time} )
  # future shows
  future_shows_list = []
  future_shows_db = Show.query.filter(Show.start_time >= datetime.now(), Show.artist_id == artist_id).all()
  for show in future_shows_db:
      venue = Venue.query.get(show.venue_id)
      future_shows_list.append( {'venue_id': show.venue_id, 'venue_name': venue.name, 'venue_image_link': venue.image_link ,'start_time': show.start_time} )      
  data['past_shows'] = past_shows_list
  data['upcoming_shows'] = future_shows_list
  data['past_shows_count'] = len(past_shows_list)
  data['upcoming_shows_count'] = len(future_shows_list)
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  # TODO: populate form with fields from artist with ID <artist_id>
  # done.
  data = Artist.query.get(artist_id)
  artist={
      "id": data.id,
      "name": data.name,
      "genres": data.genres.replace('{', '').replace('}', '').split(','),
      "city": data.city,
      "state": data.state,
      "phone": data.phone,
      "website": data.website_link,
      "facebook_link": data.facebook_link,
      "seeking_venue": data.seeking_venue,
      "seeking_description": data.seeking_description,
      "image_link": data.image_link
    }
  form = ArtistForm(name=data.name,
                    city=data.city,
                    state=data.state,
                    phone=data.phone,
                    facebook_link=data.facebook_link,
                    website_link=data.website_link,
                    image_link=data.image_link,
                    seeking_venue=data.seeking_venue,
                    seeking_description=data.seeking_description)
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  # done.
  try:
    artist = Artist.query.get(artist_id)
    artist.name = request.form['name']
    artist.city =request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.image_link = request.form['image_link']
    artist.facebook_link = request.form['facebook_link']
    artist.genres = request.form.getlist('genres')
    artist.website_link = request.form['website_link']
    artist.seeking_venue = request.form.get('seeking_venue') == 'y'
    artist.seeking_description = request.form['seeking_description']
    db.session.commit()          
    # on successful db insert, flash success
    flash('Aritst ' + str(artist_id) + ' was successfully updated!')
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + str(artist_id) + ' could not be updated.')
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  # TODO: populate form with values from venue with ID <venue_id>
  # done.
  data = Venue.query.get(venue_id)
  venue={
    "id": data.id,
    "name": data.name,
    "genres": data.genres.replace('{', '').replace('}', '').split(','),
    "address": data.address,
    "city": data.city,
    "state": data.state,
    "phone": data.phone,
    "website": data.website_link,
    "facebook_link": data.facebook_link,
    "seeking_talent": data.seeking_talent,
    "seeking_description": data.seeking_description,
    "image_link": data.image_link
  }
  form = VenueForm( name=data.name,
                    city=data.city,
                    state=data.state,
                    address=data.address,
                    phone=data.phone,
                    facebook_link=data.facebook_link,
                    website_link=data.website_link,
                    image_link=data.image_link,
                    seeking_talent=data.seeking_talent,
                    seeking_description=data.seeking_description)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  # done.
  try:
    venue = Venue.query.get(venue_id)
    venue.name = request.form['name']
    venue.city =request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    venue.image_link = request.form['image_link']
    venue.facebook_link = request.form['facebook_link']
    venue.genres = request.form.getlist('genres')
    venue.website_link = request.form['website_link']
    venue.seeking_talent = request.form.get('seeking_talent') == 'y'
    venue.seeking_description = request.form['seeking_description']
    db.session.commit()          
    # on successful db insert, flash success
    flash('Venue ' + str(venue_id) + ' was successfully updated!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + str(venue_id) + ' could not be updated.')
  finally:
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  try:      
    artist = Artist(name = request.form['name'],
                    city = request.form['city'],
                    state = request.form['state'],
                    phone = request.form['phone'],
                    image_link = request.form['image_link'],
                    facebook_link = request.form['facebook_link'],
                    genres = request.form.getlist('genres'),
                    website_link = request.form['website_link'],
                    seeking_venue = request.form.get('seeking_venue') == 'y',
                    seeking_description = request.form['seeking_description'] )
    db.session.add(artist)
    db.session.commit()          
    # # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  # done.
  raw_shows = Show.query.all()
  data = []
  for show in raw_shows:
      artist = Artist.query.get(show.artist_id)
      venue  = Venue.query.get(show.venue_id)
      data.append( {"venue_id": show.venue_id,
                    "venue_name": venue.name,
                    "artist_id": show.artist_id,
                    "artist_name": artist.name,
                    "artist_image_link": artist.image_link,
                    "start_time": show.start_time} )
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  # done.
  try:
      show = Show( artist_id  = request.form['artist_id'], 
                 venue_id   = request.form['venue_id'], 
                 start_time = request.form['start_time'] )
      db.session.add(show)
      db.session.commit()          
      # on successful db insert, flash success
      flash('Show was successfully listed!')
  except:
      db.session.rollback()
      flash('An error occurred. Show could not be listed.')
  finally:
      db.session.close()
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
