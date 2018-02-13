/**
 * Copyright Cak Juice 2016
 * untuk Nerita - Kebon Agung..
 * Gaween sakkarepmu..
 */

openerp.ka_account = function(instance, local) {
	var _t = instance.web._t,
		_lt = instance.web._lt;
	var QWeb = instance.web.qweb;

	local.userCompany = 0;
	local.templateName = 'financial_report';
	local.modelName = 'accounting.report';
	local.modelId = 1;
    local.reportType = '';
	local.statusReady = false;
	local.lastCompany = null;

	local.setInitData = function(self) {
		self.title = 'Financial Report';
		self.icon1 = 'fa fa-calendar-check-o';
		self.icon2 = 'fa fa-calendar-plus-o';
		self.icon3 = 'fa fa-print';
		self.filter1 = 'Bulan';
		self.childFilter1 = [];
		var bulanName = ['-- Semua Bulan --', 'Januari', 'Pebruari', 'Maret', 'April', 'Mei', 'Juni', 'Juli',
			'Agustus', 'September', 'Oktober', 'November', 'Desember'];
		
		for (var i=0;i<=12;i++) {
			self.childFilter1.push({li_role: '', li_class: 'child-filter-1', a_href: '#', a_html: bulanName[i], data_index: i})
		}

		self.filter2 = 'Tahun';
		self.childFilter2 = [];
	}

	local.setDefaultFilter = function(self, idxObj, idxFilter) {
		self.$('a.filter-link-'+idxFilter).each(function(index) {
			var dataIndex = parseInt($(this).attr('data-index'));
			if (dataIndex == idxObj) {
				local.linkClicked($(this), idxFilter, self);
				return false;
			}
		});
	}

	local.setStartData = function(self) {
		var d = new Date();
		var bulanIdx = d.getMonth() + 1;
		var tahunIdx = d.getFullYear();
		local.setDefaultFilter(self, bulanIdx, 1);

		var tahun = new instance.web.Model('account.move');
		tahun.call('get_year').then(function(resultsTahun) {
			self.childFilter2 = JSON.parse(resultsTahun);
			if (self.childFilter2.length > 0) {
				cf = self.childFilter2;
				for (var i=0;i<cf.length;i++) {
					var obj = '<li class="child-filter-2" role><a data-index="' + cf[i] + '" class="filter-link-2">' + cf[i] + '</a></li>';
					self.$('#ul-dropdown-2').append(obj);
				}

				local.setDefaultFilter(self, tahunIdx, 2);
			}

			resultsTahun = null;

			var user = new instance.web.Model('res.users');
			user.call('get_current_user').then(function(resultUser) {
				resultUser = JSON.parse(resultUser);
				local.userCompany = resultUser.company_id;
					
				var company = new instance.web.Model('res.company');
				company.query(['id', 'name'])
					.all()
					.then(function(resultsCompany) {
						if (resultsCompany.length > 1) {
							self.$('#submit-filter-list').append('<button class="btn btn-primary submit-filter" data-company-id="0">KONSOLIDASI</button>');
						}

						if (resultsCompany.length > 0) {
							$.each(resultsCompany, function(iterate, item) {
								var obj = ' <button class="btn btn-primary submit-filter" data-company-id="' + item.id + '">' + item.name + '</button>';
								if (resultsCompany.length > 1) {
									self.$('#submit-filter-list').append(obj);
								}
							});

							local.getReport(local.userCompany, false);
						}

						resultsCompany = null;
						local.statusReady = true;
					});

				resultUser = null;
			});
		});
	}

	local.setEventsData = function(self) {
		return {
			'click .span-caret': function(e) {
				var element = $(e.target);
				if (element.hasClass('fa-caret-down')) {
					element.removeClass('fa-caret-down');
					element.addClass('fa-caret-right');
				} else if (element.hasClass('fa-caret-right')) {
					element.removeClass('fa-caret-right');
					element.addClass('fa-caret-down');
				}
			},
			'click .filter-link-1': function(e) {
				e.preventDefault();
				local.linkClicked($(e.target), 1, self);
			},
			'click .filter-link-2': function(e) {
				e.preventDefault();
				local.linkClicked($(e.target), 2, self);
			},
			'click .submit-filter': function(e) {
				e.preventDefault();
				var obj = $(e.target);
				local.getReport(parseInt(obj.attr('data-company-id')), false, self)
			},
			'click .account-link': function(e) {
				e.preventDefault();
				var et = $(e.currentTarget);
				local.linkToAccount(et.data('id'), et.data('datefrom'), et.data('dateto'), local.lastCompany);
			},
			'click #btn_pdf_download': function(e) {
				e.preventDefault();
				local.getReport(local.lastCompany, true);
			},
		};
	}

	local.linkToAccount = function(accountId, dateFrom, dateTo, companyId) {
		var am = new instance.web.ActionManager(this);
		var detail_report_obj = new instance.web.Model('financial.report.detail.wizard');
		var create_vals = {financial_report_id: accountId, date_from: dateFrom, date_to: dateTo, company_id: companyId};

		return detail_report_obj.call('create', [create_vals]).then(function(result) {
			am.init();
			am.start();
			action = {
				type: 'ir.actions.act_window',
				name: 'Financial Report Details',
				res_model: 'financial.report.detail.wizard',
				view_mode: 'form,tree',
				view_type: 'form',
				res_id: result,
				views: [[false, 'form']],
				target: 'new',
				flags: {'form': {"initial_mode": "view",}},
			}

			var add_context = {
				account_report_id: parseInt(accountId),
				date_from: dateFrom,
				date_to: dateTo
				}
			am.do_action(action, {additional_context: add_context});
		});
	}

	local.linkClicked = function(obj, idxLink, self) {
		self.$('a.filter-link-' + idxLink).each(function(iterate) {
			if ($(this).hasClass('selected') && $(this) != obj) {
				$(this).removeClass('selected');
			}
		});

		if (!obj.hasClass('selected')) obj.addClass('selected');

		self.$('#dropdown-toggle-' + idxLink).attr('data-index', obj.attr('data-index'));
		self.$('#child-text-' + idxLink).html(obj.html());

		// if (local.statusReady && $('.submit-filter').length <= 0) {
		if (local.statusReady) {
			local.getReport(local.userCompany);
		}
	}

	local.getReport = function(company, isPrintPdf) {
		isPrintPdf = isPrintPdf || false;
		var params = local.getParams();
		params.company = company;
		local.lastCompany = company;
		local.getContent(params, isPrintPdf);
	}

	local.getParams = function() {
		var filter1Value = parseInt($('#dropdown-toggle-1').attr('data-index'));
		var filter2Value = parseInt($('#dropdown-toggle-2').attr('data-index'));

		return {
			month: filter1Value,
			year: filter2Value,
		};
	}

	local.getContent = function(params, isPrintPdf) {
		if (!params.month || !params.year || params.year <= 2000) {
			return;
		}

		isPrintPdf = isPrintPdf || false;

		var month = params.month;
		var year = params.year;
		var company = params.company;

		var modelReportName = local.reportType === 'balancesheet_horizontal' ? 'report.ka_account.report_financial_landscape_view' : 'report.ka_account.report_financial_portrait_view';
		var content = new instance.web.Model(modelReportName);

		var self = this;
		if (isPrintPdf) {
			content.call('get_pdf_financial_report', [local.modelName, local.reportType, local.modelId, month, year, company]).then(function(actions) {
				var am = new instance.web.ActionManager(self);
				am.init();
				am.start();
				am.do_action(actions);
			});
			return;
		}
		
		$('#report-content').html('<h3>Sedang memuat report...</h3>');
		content.call('get_html_financial_report', [local.modelName, local.reportType, local.modelId, month, year, company]).then(function(results) {
			results = results.trim();
			var page = $(results).find('div.page');
			if (page && page.length > 0) {
				$('#report-content').html(page[0]);
			} else {
				$('#report-content').html('<h3>Data tidak ditemukan.</h3>');
			}
		});
	}

	local.profitLossReport = instance.Widget.extend({
		template: local.templateName,
		init: function(parent) {
			this._super(parent);
			local.modelId = 52;
            local.reportType = 'profitloss';
			local.setInitData(this);
		},
		start: function() {
			local.setStartData(this);
		},
		events: local.setEventsData(this),
	});

	local.profitLossReportByStasiun = instance.Widget.extend({
		template: local.templateName,
		init: function(parent) {
			this._super(parent);
			local.modelId = 51;
            local.reportType = 'profitloss';
			local.setInitData(this);
		},
		start: function() {
			local.setStartData(this);
		},
		events: local.setEventsData(this),
	});

	local.balanceSheetReport = instance.Widget.extend({
		template: local.templateName,
		init: function(parent) {
			this._super(parent);
			local.modelId = 98;
            local.reportType = 'balancesheet_vertical';
			local.setInitData(this);
		},
		start: function() {
			local.setStartData(this);
		},
		events: local.setEventsData(this),
	});

	local.balanceSheetHorizontalReport = instance.Widget.extend({
		template: local.templateName,
		init: function(parent) {
			this._super(parent);
			local.modelId = 98;
            local.reportType = 'balancesheet_horizontal';
			local.setInitData(this);
		},
		start: function() {
			local.setStartData(this);
		},
		events: local.setEventsData(this),
	});

	local.cashFlowReport = instance.Widget.extend({
		template: local.templateName,
		init: function(parent) {
			this._super(parent);
			local.modelId = 184;
            local.reportType = 'cashflow';
			local.setInitData(this);
		},
		start: function() {
			local.setStartData(this);
		},
		events: local.setEventsData(this),
	});

	local.arusKasReport = instance.Widget.extend({
		template: local.templateName,
		init: function(parent) {
			this._super(parent);
			local.modelId = 8696;
            local.reportType = 'arus_kas';
			local.setInitData(this);
		},
		start: function() {
			local.setStartData(this);
		},
		events: local.setEventsData(this),
	});

	instance.web.client_actions.add('report.profit_loss_report', 'instance.ka_account.profitLossReport');
	instance.web.client_actions.add('report.profit_loss_report_by_stasiun', 'instance.ka_account.profitLossReportByStasiun');
	instance.web.client_actions.add('report.balance_sheet_report', 'instance.ka_account.balanceSheetReport');
	instance.web.client_actions.add('report.balance_sheet_horizontal_report', 'instance.ka_account.balanceSheetHorizontalReport');
	instance.web.client_actions.add('report.cash_flow_report', 'instance.ka_account.cashFlowReport');
	instance.web.client_actions.add('report.arus_kas_report', 'instance.ka_account.arusKasReport');
}