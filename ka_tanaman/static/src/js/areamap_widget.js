/**
* A menu that lets a user delete a selected vertex of a path.
* @constructor
*/

function DeleteVertexMenu() {
	if (typeof google === 'undefined' || !google) return;

	this.div_ = document.createElement('div');
	this.div_.className = 'delete-menu';
	this.div_.innerHTML = 'Hapus';

	var menu = this;
	google.maps.event.addDomListener(this.div_, 'click', function() {
		menu.removeVertex();
	});
}

function initDeleteVertexMenu() {
	DeleteVertexMenu.prototype = new google.maps.OverlayView();

	DeleteVertexMenu.prototype.onAdd = function() {
		var deleteMenu = this;
		var map = this.getMap();
		this.getPanes().floatPane.appendChild(this.div_);

		// mousedown anywhere on the map except on the menu div will close the menu.
		this.divListener_ = google.maps.event.addDomListener(map.getDiv(), 'mousedown', function(e) {
			if (e.target != deleteMenu.div_) {
				deleteMenu.close();
			}
		}, true);
	};

	DeleteVertexMenu.prototype.onRemove = function() {
		google.maps.event.removeListener(this.divListener_);
		this.div_.parentNode.removeChild(this.div_);

		// clean up
		this.set('position');
		this.set('path');
		this.set('vertex');
	};

	DeleteVertexMenu.prototype.close = function() {
		this.setMap(null);
	};

	DeleteVertexMenu.prototype.draw = function() {
		var position = this.get('position');
		var projection = this.getProjection();

		if (!position || !projection) {
			return;
		}

		var point = projection.fromLatLngToDivPixel(position);
		this.div_.style.top = point.y + 'px';
		this.div_.style.left = point.x + 'px';
	};

	/**
	* Opens the menu at a vertex of a given path.
	*/
	DeleteVertexMenu.prototype.open = function(map, path, vertex) {
		this.set('position', path.getAt(vertex));
		this.set('path', path);
		this.set('vertex', vertex);
		this.setMap(map);
		this.draw();
	};

	/**
	* Deletes the vertex from the path.
	*/
	DeleteVertexMenu.prototype.removeVertex = function() {
		var path = this.get('path');
		var vertex = this.get('vertex');

		if (!path || vertex == undefined) {
			this.close();
			return;
		}

		path.removeAt(vertex);
		this.close();
	};
}

odoo.define('ka_tanaman.areamap', function(require) {
	'use strict';

	var core = require('web.core');
	var Model = require('web.Model');
	var common = require('web.form_common');
	var QWeb = core.qweb;

	var AreamapWidget = common.AbstractField.extend(common.ReinitializeFieldMixin, {
		template: 'AreamapWidget',
		
		containerId: 'view-areamap',
		gmapHelpers: null,
		center: [],
		isDrawPolygon: false,
		// isEditPolygon: false,
		polygonDraw: null,
		// isEnableDraw: true,
		// gpsPolygon: null,
		dataIntersect: null,
		flagInitialize: false,
		
		events: {
			'change': 'store_dom_value',
			'click #submit_input': 'on_submit_input',
		},

		on_submit_input: function() {
			var $latitude = $('#input_latitude').val();
			var $longitude = $('#input_longitude').val();
			if ($.isNumeric($latitude) && $.isNumeric($longitude)) {
				this.gmapHelpers.createSearchMarker(parseFloat($latitude), parseFloat($longitude), color.search.icon);
			} else {
				alert("Koordinat Latitude & Longitude tidak valid!");
			}
		},

		set_default_value: function() {
			this.center = [];
			this.isDrawPolygon = false;
			this.polygonDraw = null;
			this.dataIntersect = null;

			// remove old element map container
			if ($('#view-areamap').length) {
				$('#view-areamap').remove();
			}
		},

		/*
		 * inherited
		 */
		commit_value: function () {
			if (!this.get('effective_readonly')) {
				this.store_dom_value();
			}
			return this._super();
		},

		/*
		 * inherited
		 */
		render_value: function() {
			this.gmapHelpers = new GmapHelpers();
			if (!map.status) {
				this.gmapHelpers.init();
				map.status = true;
			}

			var self = this;
			self.set_default_value();
			self.$el.empty();
			self.$el.append(QWeb.render('AreamapContainer'));

			var data = self.view.datarecord;

			// store data to global variable, because arearehab require single map data; 
			mapRehab = data;

			if (self.view.get('actual_mode') === 'create') {
				self.$el.prepend(QWeb.render('FormAreamapWidget'));

				self.isDrawPolygon = true;
				var model = new Model('res.company');
				var cid = data.company_id instanceof Array ? data.company_id[0] : data.company_id;
				model.call('read', [cid, ['name', 'latitude', 'longitude']])
					.then(function(results) {
						if (results[0].latitude != 0 && results[0].longitude != 0) {
							self.center = [results[0].latitude, results[0].longitude];
						}
						self.start_map();
					});
				return;
			}

			var gpsPolygon = data.gps_polygon ? JSON.parse(data.gps_polygon) : null;
			
			if (typeof gpsPolygon === 'undefined' || gpsPolygon == null || !gpsPolygon) return;
			
			self.center = GmapHelpers.getCenterValue(gpsPolygon);

			if (data.area_intersect_id) {
				var model = new Model('ka_plantation.area');
				var aid = data.area_intersect_id[0];
				model.call('read', [aid, ['code', 'owner', 'desa_name', 'kecamatan_name', 'kabupaten_name', 'luas', 'gps_polygon']])
					.then(function(results) {
						if (results[0].gps_polygon) {
							self.dataIntersect = results[0];
						}
						self.start_map();
					});
			} else {
				self.start_map();
			}
		},

		/*
		 * inherited
		 */
		store_dom_value: function() {
			if (this.isDrawPolygon) {
				if (!this.gmapHelpers.polygonDraw) return;
				this.internal_set_value(JSON.stringify(this.gmapHelpers.polygonDraw));
				this.gmapHelpers.resetPolygonDraw();
				return;
			}
			
			var polygonEdit = this.gmapHelpers.getPolygonEditValue();
			if (polygonEdit == null) return;

			this.internal_set_value(JSON.stringify(polygonEdit));
		},

		/*
		 * Starting map
		 */
		start_map: function() {
			var self = this;
			if (!isGmapLoaded) {
				setTimeout(function() {
					self.start_map();
				}, 1000);
				return;
			}

			self.create_map();
			initDeleteVertexMenu();
		},

		/*
		 * Create Map
		 */
		create_map: function() {
			var gmapContainer = document.getElementById(this.containerId);

			var self = this;
			if (typeof gmapContainer === 'undefined' || gmapContainer == null || !gmapContainer) {
				setTimeout(function() {
					self.create_map();
				}, 500);
				return;
			}

			var zoom = 8;
			var centerLatitude = -7.261581;
			var centerLongitude = 110.6431853;
			
			if (this.center.length > 0) {
				centerLatitude = self.center[0];
				centerLongitude = self.center[1];
				zoom = 17;
			}

			self.gmapHelpers.createMap(gmapContainer, centerLatitude, centerLongitude, zoom);
			
			if (this.view.get('actual_mode') === 'create') {
				self.gmapHelpers.drawPolygon();
				return;
			}

			self.create_polygon();
			self.create_marker();
		},

		/*
		 * Create Polygon
		 */
		create_polygon: function() {
			// create intersect polygon first if exists
			if (this.dataIntersect != null) {
				var dataIntersect = this.dataIntersect;
				var objIntersect = GmapHelpers.convertArrayToObject(JSON.parse(dataIntersect.gps_polygon));
				var colorIntersect = color.intersect.code;
				var dataIntersectInfoWindowString = 'Kode Lahan: <b>' + dataIntersect.code + '</b><br>';
				if (dataIntersect.farmer_id && dataIntersect.farmer_id.length > 1) {
					dataIntersectInfoWindowString += 'No. Induk Petani: <b>' + dataIntersect.farmer_id[1] + '</b><br>';
				}
				dataIntersectInfoWindowString += 'Desa: <b>' + dataIntersect.desa_name + '</b><br>' +
					'Kecamatan: <b>' + dataIntersect.kecamatan_name + '</b><br>' +
					'Kabupaten: <b>' + dataIntersect.kabupaten_name + '</b><br>' +
					'Luas Lahan: <b>' + dataIntersect.luas + '</b><br>';

				this.gmapHelpers.createPolygon(objIntersect, colorIntersect, dataIntersectInfoWindowString);
			}

			var data = this.view.datarecord;
			var objPolygon = GmapHelpers.convertArrayToObject(JSON.parse(data.gps_polygon));
			var strokeColor;
			if (data.status_polygon == 'valid') {
				strokeColor = color.belumtebang.code;
			} else {
				strokeColor = color.notvalid.code;
			}

			var dataInfoWindowString = 'Kode Lahan: <b>' + data.code + '</b><br>';
			if (data.farmer_id && data.farmer_id.length > 1) {
				dataInfoWindowString += 'No. Induk Petani: <b>' + data.farmer_id[1] + '</b><br>';
			}

			dataInfoWindowString += 'Desa: <b>' + data.desa_name + '</b><br>' +
				'Kecamatan: <b>' + data.kecamatan_name + '</b><br>' +
				'Kabupaten: <b>' + data.kabupaten_name + '</b><br>' +
				'Luas Lahan: <b>' + data.luas + '</b><br>';

			this.gmapHelpers.createPolygon(objPolygon, strokeColor, dataInfoWindowString, this.view.get('actual_mode') === 'edit');
		},

		/*
		 * Create Marker
		 */
		create_marker: function() {
			var data = this.view.datarecord;
			if (!data.gps_polygon) return;

			var center = GmapHelpers.getCenterValue(JSON.parse(data.gps_polygon));
			var latitude = center[0];
			var longitude = center[1];

			var iconPath;
			if (data.status_polygon == 'valid') {
				iconPath = color.belumtebang.icon;
			} else {
				iconPath = color.notvalid.icon;
			}

			this.gmapHelpers.createMarker(latitude, longitude, iconPath);
		}
	});

	core.form_widget_registry.add('areamap', AreamapWidget);
});