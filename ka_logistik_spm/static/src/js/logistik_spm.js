/*
Purpose : show toggle button on depreciation/installment lines for posted/unposted line.
Details : called in list view with "<button name="create_move" type="object" widget="WidgetAttachmentButton"/>",
    this will call the method create_move on the object account.asset.depreciation.line
*/

odoo.define('ka_logistik_spm.widget', function(require) {
"use strict";

	var core = require('web.core');
	var QWeb = core.qweb;
	var session = require('web.session');

	var _t = core._t;

	var WidgetAttachmentButton = core.list_widget_registry.get('field').extend({
		format: function(row_data, options) {
			this._super.apply(this, arguments);
			this.is_attachment = !!row_data.doc_count.value;
			var class_color = '';
			var btn_title = 'Buat Lampiran';
			if (this.is_attachment){
				class_color = 'o_is_posted';
				btn_title = 'Buka Lampiran : ' + row_data.doc_count.value;
			}
			else{class_color = 'o_unposted';}
			var ret = $('<div/>').append($('<button/>', {
				type: 'button',
				title: _t(btn_title),
				'class': 'btn btn-link fa fa-paperclip btn-sm o_ka_widgetbutton ' + class_color,
			})).html();
			return ret;
		},
	});
	
	var WidgetSendButton = core.list_widget_registry.get('field').extend({
		format: function(row_data, options) {
			this._super.apply(this, arguments);
			this.request_code_sent = !!row_data.request_code_sent.value;
			this.product_id = !!row_data.product_id.value;
			var class_color = '';
			var btn_title = '';
			if (this.request_code_sent){
				class_color = 'o_unposted';
				btn_title = 'Sudah Terkirim';
			}
			else{
				btn_title = 'Kirim Permintaan Kode Barang Baru';
				class_color = 'o_is_posted';
				}
			var ret = $('<div/>').append((!this.product_id)? $('<button/>', {
				type: 'button',
				title: _t(btn_title),
				'class': 'btn btn-link fa fa-envelope btn-sm o_ka_widgetbutton ' + class_color,
			}): '').html();
			return ret;
		},
	});

core.list_widget_registry.add("button.ka_widget_attachment_button", WidgetAttachmentButton);
core.list_widget_registry.add("button.ka_widget_send_button", WidgetSendButton);
});
