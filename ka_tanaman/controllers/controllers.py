# -*- coding: utf-8 -*-
from odoo import http
from odoo.addons.web.controllers.main import serialize_exception,content_disposition
import gpxpy 
import gpxpy.gpx

class KaPlantation(http.Controller):
	@http.route('/web/ka_plantation/area/download', type='http', auth='user')
	def download_area(self, id, **kw):
		if not id:
			return http.request.not_found()

		area = http.request.env['ka_plantation.area'].browse(int(id))

		if not area:
			return http.request.not_found()
		
		filename = 'export_' + area.code + '.gpx'
		data_gps = area.gps_mirror
		gpx = gpxpy.gpx.GPX() 

		# Create first track in our GPX: 
		gpx_track = gpxpy.gpx.GPXTrack() 
		gpx.tracks.append(gpx_track) 

		# Create first segment in our GPX track: 
		gpx_segment = gpxpy.gpx.GPXTrackSegment() 
		gpx_track.segments.append(gpx_segment) 

		# Create points:
		split_data_gps = data_gps.replace('[','').split('],')
		list_data_gps = [map(float, s.replace(']','').split(',')) for s in split_data_gps]
		for i in list_data_gps: 
			gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(i[0], i[1])) 

		filecontent = gpx.to_xml()
		return http.request.make_response(filecontent, 
			[('Content-Type', 'application/octet-stream'), ('Content-Disposition', content_disposition(filename))])


class KaPlantation_wizard(http.Controller):
	@http.route('/web/ka_plantation/area/print_polygon', type='http', auth='user')
	def print_polygon(self, id, **kw):
		if not id:
			return http.request.not_found()

		print_id = http.request.env['ka_plantation.area.print.polygon'].browse(int(id))

		if not print_id:
			return http.request.not_found()

		kategori_name = None
		kategori_id = None
		if print_id.pilih_kategori == 'desa':
			kategori_name = print_id.desa_id.name
			kategori_id = print_id.desa_id.id
		if print_id.pilih_kategori == 'kecamatan':
			kategori_name = print_id.kecamatan_id.name
			kategori_id = print_id.kecamatan_id.id
		if print_id.pilih_kategori == 'kabupaten':
			kategori_name = print_id.kab_kota_id.name
			kategori_id = print_id.kab_kota_id.id
		
		filename = 'PLOT_' + kategori_name + '.pdf'
		filecontent = http.request.env['ka_plantation.area'].cetak_polygon(print_id.pilih_kategori,kategori_id,kategori_name)
		if filecontent == "404":
			return http.request.not_found("Data petak dalam area tersebut tidak ditemukan!!")
		else:
			pdfhttpheaders = [
				('Content-Type', 'application/pdf'),
				('Content-Length', len(filecontent)),
				('Content-Disposition', 'attachment; filename='+filename),
			]
			return http.request.make_response(filecontent, headers=pdfhttpheaders)		