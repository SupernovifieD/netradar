import json
from config import Config
from flask import Blueprint, jsonify, request
from app.models import CheckResult
from app.services.monitor import monitor

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/status', methods=['GET'])
def get_status():
    """Get current status of all services"""
    results = CheckResult.get_services_status()
    return jsonify({
        'success': True,
        'data': results
    })

@bp.route('/history', methods=['GET'])
def get_history():
    """Get recent check history"""
    limit = request.args.get('limit', 100, type=int)
    results = CheckResult.get_latest(limit)
    return jsonify({
        'success': True,
        'data': results
    })

@bp.route('/history/24h', methods=['GET'])
def get_last_24h():
    results = CheckResult.get_last_24h()
    return jsonify({
        'success': True,
        'data': results
    })


@bp.route('/service/<service>', methods=['GET'])
def get_service_history(service):
    """Get history for a specific service"""
    limit = request.args.get('limit', 50, type=int)
    results = CheckResult.get_by_service(service, limit)
    return jsonify({
        'success': True,
        'service': service,
        'data': results
    })

@bp.route('/monitor/start', methods=['POST'])
def start_monitor():
    """Start the background monitor"""
    monitor.start()
    return jsonify({
        'success': True,
        'message': 'Monitor started'
    })

@bp.route('/monitor/stop', methods=['POST'])
def stop_monitor():
    """Stop the background monitor"""
    monitor.stop()
    return jsonify({
        'success': True,
        'message': 'Monitor stopped'
    })

@bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'status': 'healthy'
    })

@bp.route('/services', methods=['GET'])
def get_services():
    with open(Config.SERVICES_FILE) as f:
        services = json.load(f)

    return jsonify({
        "success": True,
        "data": services
    })

