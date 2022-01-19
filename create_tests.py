# -*- coding: utf-8 -*-
"""
Created on Tue Oct 19 19:51:14 2021

@author: Jinjin
"""

from app import db, Venue, Show, format_datetime


# venue = Venue(name = 'abc',
#               city = 'abc',
#               state = 'abc',
#               address = 'abc',
#               phone = 'abc',
#               image_link = 'abc',
#               facebook_link = 'abc',
#               genres = 'jazz',
#               website_link = 'abc',
#               looking4talent = True,
#               seeking_description = 'ggg' )


# db.session.add(venue)
# db.session.commit()      

show = Show(artist_id=1, venue_id=1, start_time= format_datetime("2021-10-01") ) 

show2 = Show(artist_id=1, venue_id=1, start_time= format_datetime("2021-12-03") ) 

db.session.add(show2)
db.session.commit()

