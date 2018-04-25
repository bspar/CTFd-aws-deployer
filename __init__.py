from flask import render_template, request, Blueprint, session, redirect, url_for
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from CTFd.models import db, Challenges, Files, Solves, WrongKeys, Keys, Tags, Teams, Awards, Hints, Unlocks
from CTFd.utils import admins_only, is_admin, cache, authed
from CTFd.plugins import register_user_page_menu_bar

from . import utils

# might be useful to generalize this plugin some day

class Instances(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teamid = db.Column(db.Integer, db.ForeignKey('teams.id'))
    name = db.Column(db.Text)       # name is 'instID.region'
    ip = db.Column(db.Text)
    allowed = db.Column(db.Integer) # is the team allowed to use their instance?
                                    # potentially useful for time-based instances

    def __init__(self, teamid, name, ip, allowed):
        self.teamid = teamid
        self.name = name
        self.ip = ip
        self.allowed = allowed


def load(app):
    app.db.create_all()
    aws_deployments = Blueprint('aws_deployments', __name__, template_folder='templates')

    @aws_deployments.route('/admin/deployments', methods=['GET'])
    @admins_only
    def deployments():
        instances = Instances.query.all()
        statuses = utils.all_statuses()
        return render_template('instances.html', instances=instances, statuses=statuses)

    @aws_deployments.route('/admin/deployments/<int:instance_id>/delete')
    @admins_only
    def delete_instance(instance_id):
        inst = Instances.query.filter_by(id=instance_id).first()
        utils.terminate(inst.name)
        db.session.delete(inst)
        db.session.commit()
        db.session.close()
        return 'success'

    @aws_deployments.route('/admin/deployments/<int:instance_id>/stop')
    @admins_only
    def sop_instance(instance_id):
        inst = Instances.query.filter_by(id=instance_id).first()
        utils.stop(inst.name)
        return 'success'

    @aws_deployments.route('/admin/deployments/<int:instance_id>/start')
    @admins_only
    def start_instance(instance_id):
        inst = Instances.query.filter_by(id=instance_id).first()
        utils.start(inst.name)
        return 'success'

    @aws_deployments.route('/admin/deployments_teams', methods=['GET'])
    @admins_only
    def deployments_teams():
        teams = Teams.query.all()
        mapping = dict()
        for team in teams:
            inst = ''
            allowed = 0
            try:
                instance = Instances.query.filter_by(teamid=team.id).one()
                inst = instance.ip
                allowed = instance.allowed
            except NoResultFound:
                inst = 'none'
            except MultipleResultsFound:
                inst = '!!Multiple!! - ' + str(team.id)
            mapping[team.name] = [inst, allowed]
        return render_template('awsdep_teams.html', teams=teams, mapping=mapping)

    @aws_deployments.route('/admin/deployments_teams/<int:team_id>/new')
    @admins_only
    def new_deployment(team_id):
        ip, name = utils.create_instance()
        instance = Instances(teamid=team_id, name=name, ip=ip, allowed=0)
        db.session.add(instance)
        db.session.commit()
        db.session.close()
        return 'success'

    @aws_deployments.route('/admin/deployments_teams/<int:team_id>/allow')
    @admins_only
    def allow_deployment(team_id):
        inst = Instances.query.filter_by(teamid=team_id).first()
        if not inst:
            return 'fail - no instance available'
        inst.allowed = 1
        db.session.commit()
        db.session.close()
        return 'success'

    @aws_deployments.route('/admin/deployments_teams/<int:team_id>/delete')
    @admins_only
    def delete_deployment(team_id):
        inst = Instances.query.filter_by(teamid=team_id).first()
        if not inst:
            return 'fail - no instance available'
        utils.terminate(inst.name)
        db.session.delete(inst)
        db.session.commit()
        db.session.close()
        return 'success'

    @aws_deployments.route('/instance')
    def user_deployment():
        if authed():
            team = Teams.query.filter_by(id=session['id']).first()
            challenge = Challenges.query.filter_by(id=24).first()
            try:
                instance = Instances.query.filter_by(teamid=team.id).one()
            except NoResultFound:
                #solves = Solves.query.filter_by(teamid=team.id, flag='flag{{W4Y_2_b1g}}').first()
                solves = Solves.query.filter_by(teamid=team.id, chalid=challenge.id).first()
                if not solves:
                    return render_template('team_instance.html', team=team, inst=None)
                else:
                    ip, name = utils.create_instance()
                    instance = Instances(teamid=team.id, name=name, ip=ip, allowed=1)
                    db.session.add(instance)
                    db.session.commit()
            except MultipleResultsFound:
                return 'Error 420 - you should never see this. Alert BlazeCTF staff'

            if instance.ip == 'pending':
                instance.ip = utils.get_ip(instance.name)
                db.session.commit()
            return render_template('team_instance.html', team=team, inst=instance,
                    status=utils.instance_status(instance.name))

        else:
            return redirect(url_for('auth.login'))

    # init code
    register_user_page_menu_bar('Instance', 'instance')
    app.register_blueprint(aws_deployments)
