#!/usr/bin/env python
# coding=utf-8
"""This script uploads a plugin package to the plugin repository.
        Authors: A. Pasotti, V. Picavet
        git sha              : $TemplateVCSFormat
"""

import sys
import getpass
import xmlrpc.client
from optparse import OptionParser
from qgis.core import QgsMessageLog, Qgis

standard_library.install_aliases()

# Configuration
PROTOCOL = 'https'
SERVER = 'plugins.qgis.org'
PORT = '443'
ENDPOINT = '/plugins/RPC2/'
VERBOSE = False


def main(parameters, arguments):
    """Main entry point.

    :param parameters: Command line parameters.
    :param arguments: Command line arguments.
    """
    address = "{protocol}://{username}:{password}@{server}:{port}{endpoint}".format(
        protocol=PROTOCOL,
        username=parameters.username,
        password=parameters.password,
        server=parameters.server,
        port=parameters.port,
        endpoint=ENDPOINT)
    QgsMessageLog.logMessage("Connecting to: %s" % hide_password(address), 'ADV', level=Qgis.Info)

    server = xmlrpc.client.ServerProxy(address, verbose=VERBOSE)

    try:
        with open(arguments[0], 'rb') as handle:
            plugin_id, version_id = server.plugin.upload(
                xmlrpc.client.Binary(handle.read()))
        QgsMessageLog.logMessage("Plugin ID: %s" % plugin_id, 'ADV', level=Qgis.Info)
        QgsMessageLog.logMessage("Version ID: %s" % version_id, 'ADV', level=Qgis.Info)
    except xmlrpc.client.ProtocolError as err:
        QgsMessageLog.logMessage("A protocol error occurred", 'ADV', level=Qgis.Info)
        QgsMessageLog.logMessage("URL: %s" % hide_password(err.url, 0), 'ADV', level=Qgis.Info)
        QgsMessageLog.logMessage("HTTP/HTTPS headers: %s" % err.headers, 'ADV', level=Qgis.Info)
        QgsMessageLog.logMessage("Error code: %d" % err.errcode, 'ADV', level=Qgis.Info)
        QgsMessageLog.logMessage("Error message: %s" % err.errmsg, 'ADV', level=Qgis.Info)
    except xmlrpc.client.Fault as err:
        QgsMessageLog.logMessage("A fault occurred")
        QgsMessageLog.logMessage("Fault code: %d" % err.faultCode, 'ADV', level=Qgis.Info)
        QgsMessageLog.logMessage("Fault string: %s" % err.faultString, 'ADV', level=Qgis.Info)


def hide_password(url, start=6):
    """Returns the http url with password part replaced with '*'.

    :param url: URL to upload the plugin to.
    :type url: str

    :param start: Position of start of password.
    :type start: int
    """
    start_position = url.find(':', start) + 1
    end_position = url.find('@')
    return "%s%s%s" % (
        url[:start_position],
        '*' * (end_position - start_position),
        url[end_position:])


if __name__ == "__main__":
    parser = OptionParser(usage="%prog [options] plugin.zip")
    parser.add_option(
        "-w", "--password", dest="password",
        help="Password for plugin site", metavar="******")
    parser.add_option(
        "-u", "--username", dest="username",
        help="Username of plugin site", metavar="user")
    parser.add_option(
        "-p", "--port", dest="port",
        help="Server port to connect to", metavar="80")
    parser.add_option(
        "-s", "--server", dest="server",
        help="Specify server name", metavar="plugins.qgis.org")
    options, args = parser.parse_args()
    if len(args) != 1:
        QgsMessageLog.logMessage("Please specify zip file.\n", 'ADV', level=Qgis.Info)
        parser.print_help()
        sys.exit(1)
    if not options.server:
        options.server = SERVER
    if not options.port:
        options.port = PORT
    if not options.username:
        # interactive mode
        username = getpass.getuser()
        print("Please enter user name [%s] :" % username, end=' ')

        res = input()
        if res != "":
            options.username = res
        else:
            options.username = username
    if not options.password:
        # interactive mode
        options.password = getpass.getpass()
    main(options, args)
