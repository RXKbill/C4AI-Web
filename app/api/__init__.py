from flask import Blueprint

api_bp = Blueprint('api', __name__)

from . import (
    auth, user, role, menu, dept, device, alarm, data, 
    drone, feature, model, notification, rule, statistics, 
    trade, workorder
) 