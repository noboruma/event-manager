#!/usr/bin/python
from flask import Flask, json, abort, jsonify, request
from flask_restplus import Api, Resource, fields, marshal_with
import database, email_utils, config

class Service:

    def __init__(self, db_file, secret_token, smtp_context):

        service = Flask(__name__)
        service_api = Api(app = service)
        name_space = service_api.namespace('',
                description="Event Manager API",
                version = "1.0",
                title = "Event Manager")
        db_file = db_file
        self.service = service

        event_model = service_api.model('Event',
                { 'name': fields.String(description='The name of the event', required=True),
            'location': fields.String(description='The address of the event', required=True),
            'start_timestamp': fields.String(description='Start date of the event in UTC. format:YYYY-MM-DD HH:MM:SS', required=True),
            'end_timestamp' : fields.String(description='End date of the event in UTC. format:YYYY-MM-DD HH:MM:SS', required=True)})

        user_model = service_api.model('User', { 'email':
            fields.String(description='Email of the user', required=True)})

        event_added_response = service_api.model('EventAddedResponse', {"event_id" :
            fields.String(description="unique identifer of the event",
                required=True)})

        event_with_metadata = service_api.inherit('EventWithMetaData', event_model, {"id" :
            fields.String(description="unique identifer of the event",
                required=True)})

        @name_space.route('/events')
        class Events(Resource):
            @service_api.response(200, 'List of events successfully retrieved', model=[event_with_metadata])
            @service_api.response(500, 'Database error')
            @service_api.doc(description="List all events")
            @service_api.marshal_with(event_with_metadata)
            def get(self):
                conn = database.open_connection(db_file)
                with conn:
                    return database.list_events(conn), 200
                abort(500)

            @service_api.response(200, 'New event added successfully', model=event_added_response)
            @service_api.response(400, 'Invalid event parameters')
            @service_api.response(500, 'Database error')
            @service_api.doc(expect=[event_model],
                             description="Add a new event")
            @service_api.marshal_with(event_added_response)
            def post(self):
                conn = database.open_connection(db_file)
                with conn:
                    try:
                        event_id = database.add_event_from_json(conn, request.json)
                        return {'event_id':event_id}, 200
                    except:
                        abort(400)
                abort(500)

        @name_space.route('/event/<event_id>')
        class Event(Resource):
            @service_api.doc(params={'event_id': 'Event unique identifier'},
                             description="Get event data from its ID")
            @service_api.response(200, 'Event data retrieved successfully', model=event_with_metadata)
            @service_api.response(500, 'Database error')
            @service_api.marshal_with(event_with_metadata)
            def get(self, event_id):
                conn = database.open_connection(db_file)
                with conn:
                    try:
                        return database.get_event(conn, event_id), 200
                    except:
                        abort(400)
                abort(500)

            @service_api.doc(params={'event_id': 'Event unique identifier'},
                             description="Delete an event")
            @service_api.response(200, 'Event deleted successfully')
            @service_api.response(400, 'Non existing event id')
            @service_api.response(500, 'Database error')
            def delete(self, event_id):
                conn = database.open_connection(db_file)
                with conn:
                    try:
                        database.delete_event(conn, event_id)
                        return {}
                    except database.NonExistingError:
                        abort(400)
                abort(500)

        @name_space.route('/users/<user_email>')
        class list_user_events(Resource):
            @service_api.doc(params={'user_email': 'Email address used to register events'},
                             description="List all the events registered by a user")
            @service_api.response(200, 'Users\' events retrieved successfully',
                    model=[event_with_metadata])
            @service_api.response(500, 'Database error')
            @service_api.marshal_with(event_with_metadata)
            def get(self, user_email):
                conn = database.open_connection(db_file)
                with conn:
                    return database.list_user_events(conn, user_email), 200
                abort(500)

        @name_space.route('/register/<user_email>/<event_id>')
        class register_user(Resource):
            @service_api.doc(params={'user_email': 'Email address to add to the event',
                                     'event_id': 'Event unique identifier'},
                                     description="Register an user to an event")
            @service_api.response(200, 'User successfully registered to the event')
            @service_api.response(400, 'Non existing event id')
            @service_api.response(500, 'Database error')
            def post(self, user_email, event_id):
                conn = database.open_connection(db_file)
                with conn:
                    # Automatically register user in DB
                    try:
                        database.register_user(conn, user_email, event_id)
                    except database.DuplicateError:
                        # Ignore if duplicate
                        pass
                    try:
                        database.register_event(conn, user_email, event_id)
                        event = database.get_event(conn, event_id)
                        email_utils.send_notification(smtp_context, user_email,
                                event_id)
                        email_utils.send_calendar_invite(smtp_context, user_email,
                                event)
                    except database.NonExistingError:
                        name_space.abort(400)
                    except database.DuplicateError:
                        # Ignore if duplicate
                        pass
                    return {}
                abort(500)

            @service_api.doc(params={'user_email': 'Email address used to unregister events',
                                     'event_id': 'Event unique identifier'},
                                     description="Unregister an user from an event")
            @service_api.response(200, 'User successfully unregistered from the event')
            @service_api.response(400, 'Non existing event id')
            @service_api.response(500, 'Database error')
            def delete(self, user_email, event_id):
                conn = database.open_connection(db_file)
                with conn:
                    try:
                        database.unregister_event(conn, user_email, event_id)
                    except database.NonExistingError:
                        abort(400)
                    return {}
                abort(500)

        @name_space.route('/admin/<token>/<event_id>')
        class Admin(Resource):
            @service_api.doc(params={'token': 'Secret token',
                                     'event_id': 'Event unique identifier'},
                                     description="Register an user to an event")
            @service_api.response(200, 'List of users successfully retrieved', model=[user_model])
            @service_api.response(401, 'Unauthorized')
            @service_api.response(400, 'Event does not exist')
            @service_api.response(500, 'Database error')
            @service_api.doc(description="List all users going to an event")
            @service_api.marshal_with(user_model)
            def get(self, token, event_id):
                conn = database.open_connection(db_file)
                if token != secret_token:
                    abort(401)
                with conn:
                    try:
                        return database.get_users_attending_event(conn, event_id), 200
                    except database.NonExistingError:
                        abort(400)
                abort(500)

    def get_test_client(self):
        return self.service.test_client()

    def run(self):
        import os
        port = int(os.environ.get('PORT', 5000))
        self.service.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    (db_file, secret_token, email_context) = config.get_config('configs/prod.ini')
    s = Service(db_file, secret_token, email_context)
    s.run()
