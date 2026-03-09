import ibm_db
from flask_restful import Resource
from flask_httpauth import HTTPBasicAuth
from bdp_auth import BDPAuth
from bdp_dbutil import BDPDBConnection, getTableName

auth = HTTPBasicAuth()
authF = BDPAuth()


@auth.verify_password
def verify(username, password):
    return authF.auth(username, password)


def _fetch_all(stmt):
    rows = []
    row = ibm_db.fetch_assoc(stmt)
    while row:
        # Convert non-serialisable types to str
        rows.append({k: (str(v) if v is not None and not isinstance(v, (int, float, str, bool)) else v)
                     for k, v in row.items()})
        row = ibm_db.fetch_assoc(stmt)
    return rows


class BDPDashboardTenants(Resource):
    @auth.login_required
    def get(self):
        try:
            conn = BDPDBConnection.getInstance().getDBConnection()
            stmt = ibm_db.exec_immediate(conn, "SELECT * FROM " + getTableName("BDP_TENANT"))
            return _fetch_all(stmt)
        except Exception as e:
            return {"error": str(e)}, 500


class BDPDashboardHardware(Resource):
    @auth.login_required
    def get(self):
        try:
            conn = BDPDBConnection.getInstance().getDBConnection()
            sql = (
                "SELECT h.*, "
                "  (SELECT READING FROM " + getTableName("BDP_RAW_EVENTS") +
                "   WHERE HARDWARE_UID = h.HARDWARE_UID "
                "   ORDER BY READING_TIME DESC FETCH FIRST 1 ROWS ONLY) AS LAST_READING, "
                "  (SELECT READING_TIME FROM " + getTableName("BDP_RAW_EVENTS") +
                "   WHERE HARDWARE_UID = h.HARDWARE_UID "
                "   ORDER BY READING_TIME DESC FETCH FIRST 1 ROWS ONLY) AS LAST_READING_TIME "
                "FROM " + getTableName("BDP_HARDWARE") + " h "
                "ORDER BY h.HARDWARE_UID"
            )
            stmt = ibm_db.exec_immediate(conn, sql)
            return _fetch_all(stmt)
        except Exception as e:
            return {"error": str(e)}, 500


class BDPDashboardIncidents(Resource):
    @auth.login_required
    def get(self):
        try:
            conn = BDPDBConnection.getInstance().getDBConnection()
            sql = (
                "SELECT i.*, h.HARDWARE_ID, h.HARDWARE_TYPE, h.HARDWARE_DETAIL "
                "FROM " + getTableName("BDP_INCIDENT") + " i "
                "JOIN " + getTableName("BDP_HARDWARE") + " h ON i.CAUSE_HARDWARE = h.HARDWARE_UID "
                "ORDER BY i.INCIDENT_TIME DESC FETCH FIRST 100 ROWS ONLY"
            )
            stmt = ibm_db.exec_immediate(conn, sql)
            return _fetch_all(stmt)
        except Exception as e:
            return {"error": str(e)}, 500


class BDPDashboardEvents(Resource):
    @auth.login_required
    def get(self, hardware_uid):
        try:
            conn = BDPDBConnection.getInstance().getDBConnection()
            sql = (
                "SELECT READING_TIME, READING FROM " + getTableName("BDP_RAW_EVENTS") +
                " WHERE HARDWARE_UID = " + str(int(hardware_uid)) +
                " ORDER BY READING_TIME DESC FETCH FIRST 120 ROWS ONLY"
            )
            stmt = ibm_db.exec_immediate(conn, sql)
            return _fetch_all(stmt)
        except Exception as e:
            return {"error": str(e)}, 500
