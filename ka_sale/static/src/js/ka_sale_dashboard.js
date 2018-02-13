odoo.define('ka_sale.dashboard', function (require) {
	"use strict";

	var core = require('web.core');
	var data = require('web.data');
	var Model = require('web.DataModel');
	var utils = require('web.utils');
	var KanbanView = require('web_kanban.KanbanView');

	var QWeb = core.qweb;

	var _t = core._t;
	var _lt = core._lt;

	var salesOrderDashboard = KanbanView.extend({
		display_name: _lt('Dashboard'),
		events: {
	        'click .so-target': 'on_so_action_clicked',
	    },

	    render: function() {
	        var self = this;
	        this._super();
	        var x = self.$el.find('.so-target');
	        for (var i = 0; i < x.length; i++) {
	        	x[i].id = x[i].firstElementChild.innerHTML
	        }
	    },

	    on_so_action_clicked: function(ev) {
	    	var self = this;
	    	var $target = $(ev.currentTarget);
	    	var id =parseInt($target.attr('id'));
	    	return this.do_action({
			    type: 'ir.actions.act_window',
				res_model: 'sale.order',
				res_id: id,
				view_mode: 'form',
                view_type: 'form',
				views: [[false, 'form']],
				target: 'current',
			});
	    },
	});

	core.view_registry.add('ka_sale_dashboard_view', salesOrderDashboard);
	return salesOrderDashboard;
});
