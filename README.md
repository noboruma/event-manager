# Event manager
Author: Thomas Legris

[![Build Status](https://travis-ci.com/noboruma/event-manager.svg?branch=main)](https://travis-ci.com/noboruma/event-manager)
[![codecov](https://codecov.io/gh/noboruma/event-manager/branch/main/graph/badge.svg?token=IH7PEECRHL)](https://codecov.io/gh/noboruma/event-manager)

## How to start the application

```
$ pip3 install -r requirements.txt
$ ./run_prod.sh
```

You can modify configuration in the 'configs/prod.ini' file.
Email address and smtp server configuration can be changed there.
Current prod configuration uses "mailtrap.io"

Email templates are kept in 'email_utils.py' and can be modified there.

### API

When the server is running, go to https://127.0.0.1:5000
Or go to http://top-event-manager.herokuapp.com/ (please note the HTTP, not HTTPS)

#### API Decisions

Double registrations are not treated as errors. It will silently do nothing.

Users are signed up directly when registering to an event.

## Databases

There are two data base, one named 'prod.db', which is the production DB.
The other is 'test.db', which is a duplicate of 'prod.db' but used for testing purposes.
Database usage can be configured in the config files.

## CI/CD

The project relies on travis to run the test and deploy to heroku
https://travis-ci.com/github/noboruma/event-manager

Heroku is accessible at: top-event-manager.herokuapp.com

### How to test manually

There are two events stored in the DataBase.
Users are sign up automatically when they register to an event.

Either go to the swagger API directly: https://127.0.0.1:5000

Or

List events:
```
$ curl -X GET 127.0.0.1:5000/events
```

Register to the 0123456789 event:
```
$ curl -X POST 127.0.0.1:5000/register/test@test.com/1
```

List events for a given user:
```
$ curl -X GET 127.0.0.1:5000/events/test@test.com
```

Unregister from the 0123456789 event:
```
$ curl -X DELETE 127.0.0.1:5000/register/test@test.com/1
```

List all users attending an event
```
$ curl -X GET 127.0.0.1:5000/admin/SECRET/1
```

## How to run tests

Focus was put on doing integration/functional tests of the public facing API.
This choice is purely driven by time & effort constraints.

```
$ ./run_test.sh
```

Integration tests will run against a mocked SMTP server and a mocked HTTP server.
Everything is tested locally.

# Nice to have progress

-The code should have and pass all unit tests: DONE
- The tool should have API endpoints for managing events: DONE
- The tool should have a front end (written in JS) for signing up for events / managing events: TODO
- The tool should email the provided email address with a calendar invitation to the event: HALF DONE
- The tool should have APIs (protected with an fixed API key) that allow a user to
    - See all people who signed up for an event: DONE
    - Remove an email address from an event: INDIRECTLY DONE
    - Sign up a person from an event: INDIRECTLY DONE
