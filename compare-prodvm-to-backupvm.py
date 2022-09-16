#!/usr/bin/python
#! -*- coding: utf-8 -*-

import json
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import requests
import ssl
import sqlite3
import sys
import urllib3
import xlsxwriter


class VMware:
    def __init__(self, address, login, password):
        self.address = address
        s = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        s.verify_mode = ssl.CERT_NONE

        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        self.vSphereConnection = SmartConnect(host=address,
                                              user=login,
                                              pwd=password,
                                              sslContext=context)

        self.vCenterObject = self.vSphereConnection.content

    def __del__(self):
        Disconnect(self.vSphereConnection)

    def get_vms(self, conn):
        container = self.vCenterObject.viewManager.CreateContainerView(self.vCenterObject.rootFolder, [vim.VirtualMachine], True)
        vmList = container.view
        for vm in vmList:
            try:
                rp_name = vm.resourcePool.name
            except:
                rp_name = 'UNDEFINED'
            conn.execute('INSERT INTO vms (dc, resource_pool, name) VALUES ("{}", "{}", "{}")'.format(self.address, rp_name, vm.name))


class Veeam:
    # Initialize variable and get API authorize token
    def __init__(self, address, login, password):
        urllib3.disable_warnings()

        self.address = 'https://' + address + ':9419/api/'
        self.headers = {'accept': 'application/json', 'x-api-version': '1.0-rev1', 'Content-Type': 'application/x-www-form-urlencoded'}
        self.credentials = 'grant_type=password&username=' + login + '&password=' + password + '&refresh_token=&code=&use_short_term_refresh='

        access_token = self.get_authorize_token()
        self.headers['Authorization'] = 'Bearer ' + access_token

    # Get API authorize token
    def get_authorize_token(self):
        try:
            r = requests.post(self.address + 'oauth2/token',
                              data=self.credentials,
                              headers=self.headers,
                              verify=False
                              )
            if r.status_code != 200:
                raise Exception('Authorization faileds')

            json_string = json.loads(r.text)
            return json_string['access_token']
        except Exception:
            sys.exit('Authorization faileds')

    # Get VMs in job
    def get_job_info(self, job_id, job_name, c, conn):
        r = requests.get(self.address + 'v1/backups/' + job_id + '/objects',
                         headers=self.headers,
                         verify=False
                         )
        parsed = json.loads(r.text)
        for vm in parsed['data']:
            c.execute('SELECT job_name FROM vms WHERE name = "{}"'.format(vm['name']))
            exist_job = c.fetchone()
            if exist_job == None:
                new_job_name = job_name
            else:
                if exist_job[0] != None:
                    new_job_name = exist_job[0] + ', ' + job_name
                else:
                    new_job_name = job_name
            conn.execute('UPDATE vms SET job_name = "{}" WHERE name = "{}"'.format(new_job_name, vm['name']))

    # Get jost
    def get_jobs(self, c, conn):
        r = requests.get(self.address + 'v1/backups',
                         headers=self.headers,
                         verify=False
                         )
        parsed = json.loads(r.text)
        for job in parsed['data']:
            self.get_job_info(job['id'], job['name'], c, conn)


def main():
    conn = sqlite3.connect(':memory:')
    c = conn.cursor()
    c.execute('''CREATE TABLE vms (id INTEGER PRIMARY KEY AUTOINCREMENT, dc text, resource_pool text, name text, job_name text)''')

    vmware = VMware('vcenter',
                    'login',
                    'password'
                    )
    get_vms = vmware.get_vms(conn)

    conn.commit()

    veeam = Veeam('veeam_serever',
                  'login',
                  'password'
                  )
    veeam.get_jobs(c, conn)

    conn.commit()

    c.execute("SELECT * FROM vms ORDER BY dc, resource_pool, job_name, name")
    rows = c.fetchall()

    workbook = xlsxwriter.Workbook('compare-prodvm-to-backupvm.xlsx')
    worksheet = workbook.add_worksheet()

    bold = workbook.add_format({'bold': True})
    worksheet.write('A1', 'VM name', bold)
    worksheet.write('B1', 'Resource Pool', bold)
    worksheet.write('C1', 'vCenter', bold)
    worksheet.write('D1', 'Job name', bold)

    x = 2
    for row in rows:
        worksheet.write('A'+str(x), row[3])
        worksheet.write('B'+str(x), row[2])
        worksheet.write('C'+str(x), row[1])
        worksheet.write('D'+str(x), row[4])
        x += 1

    workbook.close()
    print('Work done.')

if __name__ == "__main__":
    main()
