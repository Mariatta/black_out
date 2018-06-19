black_out
=========

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/ambv/black


This is a personal experiment, and still in progress.

I'm wanting a GitHub bot that can:

- format an entire repo using `black <https://pypi.org/project/black/>`_

- format the codes in incoming pull requests using ``black``, and only format the
  affected changed files.


Blacken an entire repo (status: done!!)
=======================================

How to blacken an entire repo initially, for a project that did not use ``black``
before? I guess someone needs to check out the repo, run ``black``, then commit
the changes and create a pull request. They need to be on a computer to do this!
😱

What if I have more than one projects to blacken? Seems like a lot of manual
boring work and potentially a lot of repetition.

So I want a bot to do those boring things.

What I had in mind:

1. deploy the bot
2. create a new issue, commanding the bot to blacken the repo
3. bot does its magic
4. profit

My bot will listen to one of the following commands as cue to start blacken the
repo:

- ``turn off the sun``
- ``take down the moon``
- ``switch off the stars``
- ``paint the sky black``
- ``black out the sun``

All stolen from `Darren Hayes <https://youtu.be/gJMNWTioW34>`_ of course.

This is now done! Issue `#5 <https://github.com/Mariatta/black_out/issues/5>`_ is an example.
I created an issue that says: "Black out the sun". The bot picks it up, ran black against
its own code, then created the `PR <https://github.com/Mariatta/black_out/pull/12>`_ containing
the formatted files.

Blacken incoming pull request
=============================

Idea
----

Once I've blacken an entire repo, perhaps it's a good idea to ensure incoming
changes are blackened too, and maybe it should be part of some CI.

I'm not aware if there's such CI yet. Seems like the recommended way is to
install `pre-commit <https://pre-commit.com/>`_, setup the configuration ``.yml``
file, and then run it. Just sounds like a lot of work to me. (I'm very lazy!)

What if anyone can write their code the way they usually do, but when they
propose the pull request, a bot can run ``black`` against the changed code,
and push the reformatted code back to the pull request?

I don't know if this is a good idea or not, but it could be fun experiment. 😄

Another thought is, instead of blacken incoming pull requests, I'll just schedule
the entire repo to be blackened once a week.

Current implementation
----------------------

I've made it such that the bot will black out a PR when the label ``black out`` is
applied.

Deployment
==========

Heroku settings
---------------

|Deploy|

.. |Deploy| image:: https://www.herokucdn.com/deploy/button.svg
   :target: https://heroku.com/deploy?template=https://github.com/mariatta/black_out

In Heroku, set the environment variables:

- ``GH_REPO_NAME``: The repository name. For example, for `https://github.com/ambv/black`,
  the repo name is ``black``.
- ``GH_REPO_FULL_NAME``: The repository full name (organization and name). For example,
  for `https://github.com/ambv/black`, the repo full name is ``ambv/black``.
- ``GH_USERNAME``: The GitHub username for the bot user. The bot user must have
  write access to the repo being blackened.
- ``GH_EMAIL``: The email address for the bot user. The bot user must have write
  access to the repo being blackened.
- ``GH_FULL_NAME``: The full name of the bot user. The bot user must have write
  access to the repo being blackened.
- ``GH_AUTH``: The oauth token for the bot user.
- ``GH_SECRET``: The GitHub webhook secret.

Add the Heroku Redis add-on, and **turn it on**.

GitHub webhook settings
-----------------------

Enable the webhook events on:

- Issues

- Pull requests (only needed to blacken incoming pull requests)


Limitations
===========

The bot needs write access to the repo to be blackened.

With the current design, I'll need to deploy an instance of ``black_out`` for every
GitHub repo I want to blacken. ☹️ It's still not what I want out of this project.
I think I'll need to make it into a `GitHub App <https://developer.github.com/apps/>`_
, but I don't yet know how to do that. 🙃
