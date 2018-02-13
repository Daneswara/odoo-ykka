odoo.define('ka_tanaman.areamap_view', function(require) {
	'use strict';

	var core = require('web.core');
	var data = require('web.data');
	var Model = require('web.DataModel');
	var View = require('web.View');
	var ActionManager = require('web.ActionManager');

	var _t = core._t;
	var _lt = core._lt;
	var QWeb = core.qweb;

	var AreamapView = View.extend({
		icon: 'fa-map-marker',
		display_name: _lt('Map'),
		view_type: 'areamap',
		template: 'AreamapView',
		fields_list: [],
		fields_string: [],

		containerId: 'areamap-all-container',
		gmapHelpers: null,
		records: null,
		strUrl: null,
		queryStrUrl: null,
		center: [-7.261581, 110.6431853],
		zoom: 8,

		events: {
			'click #submit_input_all': 'on_submit_input_all',
		},

		defaults: _.extend({}, View.prototype.defaults, {
			// records can be selected one by one
			selectable: false,
			// list rows can be deleted
			deletable: false,
			// whether the column headers should be displayed
			header: true,
			// display addition button, with that label
			addable: _lt("Create"),
			// whether the list view can be sorted, note that once a view has been
			// sorted it can not be reordered anymore
			sortable: false,
			// whether the view rows can be reordered (via vertical drag & drop)
			reorderable: true,
			action_buttons: true,
			//whether the editable property of the view has to be disabled
			disable_editable_mode: false,
		}),

		/**
		 * Render the buttons according to the ListView.buttons template and
		 * add listeners on it.
		 * Set this.$buttons with the produced jQuery element
		 * @param {jQuery} [$node] a jQuery node where the rendered buttons should be inserted
		 * $node may be undefined, in which case the ListView inserts them into this.options.$buttons
		 * if it exists
		 */
		render_buttons: function($node) {
			if (!this.$buttons) {
				this.$buttons = $(QWeb.render("ListView.buttons", {'widget': this}));
				this.$buttons.on('click', '.o_list_button_add', this.proxy('do_add_record'));
				this.$buttons.appendTo($node);
			}
		},

		/**
		 * Handles signal for the addition of a new record (can be a creation,
		 * can be the addition from a remote source, ...)
		 *
		 * The default implementation is to switch to a new record on the form view
		 */
		do_add_record: function () {
			this.select_record(null);
		},

		/**
		 * Used to handle a click on a table row, if no other handler caught the
		 * event.
		 *
		 * The default implementation asks the list view's view manager to switch
		 * to a different view (by calling
		 * :js:func:`~instance.web.ViewManager.on_mode_switch`), using the
		 * provided record index (within the current list view's dataset).
		 *
		 * If the index is null, ``switch_to_record`` asks for the creation of a
		 * new record.
		 *
		 * @param {Number|void} index the record index (in the current dataset) to switch to
		 * @param {String} [view="page"] the view type to switch to
		 */
		select_record:function (index, view) {
			view = view || index === null || index === undefined ? 'form' : 'form';
			this.dataset.index = index;
			_.delay(_.bind(function () {
				this.do_switch_view(view);
			}, this));
		},

		/*
		 * trigerred when user submit input search location
		 */
		on_submit_input_all: function() {
			var $latitude = $('#input_latitude_all').val();
			var $longitude = $('#input_longitude_all').val();
			
			if ($.isNumeric($latitude) && $.isNumeric($longitude)) {
				this.gmapHelpers.createSearchMarker(parseFloat($latitude), parseFloat($longitude), color.search.icon);
			} else {
				alert("Koordinat Latitude & Longitude tidak valid!");
			}
		},

		/*
		 * @inherited
		 */
		start: function() {
			for (var f in this.fields_view.fields) {
				var fields = this.fields_view.fields[f];
				this.fields_list.push(f);
				this.fields_string.push(fields.string);
			}

			var action = this.options.action;
			this.strUrl = '&amp;view_type=form&amp;model=ka_plantation.area&amp;menu_id=' + action.menu_id +
				'&amp;action=' + action.id;
			this.queryStrUrl = 'data-menu="' + action.menu_id + '" data-action-model="ir.actions.act_window"';
		},

		/*
		 * @inherited
		 * trigerred when user searching record
		 */
		do_search: function(domain, context, group_by) {
			var self = this;

			self.gmapHelpers = new GmapHelpers();
			if (!map.status) {
				self.gmapHelpers.init();
				map.status = true;
			}

			var model = new Model(self.model);
			model.call('search', [domain]).then(function(ids) {
				self.dataset.ids = ids;
				self.read_record();
			});
		},

		/*
		 * @inherit
		 */
		read_record: function() {
			var self = this;

			this.dataset.read_ids(this.dataset.ids, this.fields_list).done(function(records) {
				self.records = records;
				self.start_map();
			});
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
				return;``
			}

			self.gmapHelpers.createMap(gmapContainer, self.center[0], self.center[1], self.zoom);
			self.create_polygon();
		},

		/*
		 * Create Polygon
		 */
		create_polygon: function() {
			var self = this;
			_(this.records).each(function(data) {
				if (!data.gps_polygon || JSON.parse(data.gps_polygon.length) <= 0) return;

				var objPolygon = GmapHelpers.convertArrayToObject(JSON.parse(data.gps_polygon));
				var strokeColor;
				if (data.status_polygon == 'valid') {
					strokeColor = color.belumtebang.code;
				} else {
					strokeColor = color.notvalid.code;
				}

				var dataInfoWindowString = '';

				for (var i=0;i<self.fields_list.length;i++) {
					var string = self.fields_string;
					var field = self.fields_list;
					if (field[i] === 'gps_polygon' || field[i] === 'gps_mirror') continue;

					var dataField = data[field[i]] instanceof Array ? data[field[i]][1] : data[field[i]];
					dataInfoWindowString += string[i] + ': <b>' + dataField + '</b><br>';
				}

				dataInfoWindowString += '<br><b><a href="web#id=' + data.id + self.strUrl + '"' + self.queryStrUrl + ' data-action-id="' + data.id + '" target="_blank">Klik Detail Data</a></b>';
					// 'Pemilik Lahan: <b>' + data.owner + '</b><br><br>' +
					// 'Lokasi' + '<br>' +
					// 'Desa: <b>' + data.desa_name + '</b><br>' +
					// 'Kecamatan: <b>' + data.kecamatan_name + '</b><br>' +
					// 'Kabupaten: <b>' + data.kabupaten_name + '</b><br>' +
					// 'Luas Lahan: <b>' + data.luas + '</b><br>';

				self.gmapHelpers.createPolygon(objPolygon, strokeColor, dataInfoWindowString);

				self.create_marker(data);
			});
		},

		/*
		 * Create Marker
		 */
		create_marker: function(data) {
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
		},
	});

	core.view_registry.add('areamap', AreamapView);
});