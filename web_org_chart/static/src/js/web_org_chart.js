odoo.define('web_org_chart.web_org_chart', function(require){
    var core = require('web.core');
    var data = require('web.data');
    var Widget = require('web.Widget');
//    var Menu = require('web.Menu');
    var session = require('web.session');
    var common = require('web.form_common');
    var Model = require('web.DataModel');
    var QWeb = core.qweb;
    var _t = core._t;

    QWeb.add_template('/web_org_chart/static/src/xml/web_org_chart.xml');

    var org_chart_company_employee = Widget.extend({
        template: 'org_chart',

        init: function(data) {
            this.dept_data = false;
            this._super(data);
        },

        renderElement: function(id) {
            this._super();
            this.$('#type_of_dept option[value=' + id + ']').attr('selected', 'selected');
        },

        start: function(ids) {
            var self = this;
            var emp_child = [];
            var orgdiagram = null;
            var counter = 0;
            var m_timer = null;
            var fromValue = null;
            var fromChart = null;
            var toValue = null;
            var toChart = null;
            var items = {};
            
            self.dept_dataset = new data.DataSetSearch(self, 'hr.department', {}, []);
            self.dept_dataset.read_slice(['id', 'name']).then(function(records) {
                self.dept_data = records;
                var template = "";
                _.each(records, function(res) {
                    template = template + '<option value=' + res.id + '>' + res.name + '</option>'
                });
                self.$("#type_of_dept").append(template)
            });
            
            $(document).ready(function() {
                jQuery.ajaxSetup({
                    cache: false
                });
                ResizePlaceholder();
                orgdiagram = SetupWidget(self.$(".contentpanel"), "contentpanel", []);
            });
            
            function SetupWidget(element, name, id,current) {
                self.$("#print").bind('click', function() {
                    window.print();
                });
                self.$("#toogl_button").bind('click', function(e) {
                    if (self.$("#toogl_button").text().trim("") == _t('Vertical layout')) {
                        self.$(".contentpanel").orgDiagram({
                            orientationType: primitives.common.OrientationType.Left,
                            horizontalAlignment: primitives.common.HorizontalAlignmentType.Center
                        });
                        self.$(".contentpanel").orgDiagram("update", primitives.orgdiagram.UpdateMode.Refresh);
                        self.$("#toogl_button").text(_t("Horizontal layout"))
                    } else if (self.$("#toogl_button").text().trim("") == _t('Horizontal layout')) {
                        self.$(".contentpanel").orgDiagram({
                            orientationType: primitives.common.OrientationType.Top,
                            horizontalAlignment: primitives.common.HorizontalAlignmentType.Center
                        });
                        self.$(".contentpanel").orgDiagram("update", primitives.orgdiagram.UpdateMode.Refresh);
                        self.$("#toogl_button").text(_t("Vertical layout"))
                    }
                });
                
                self.$("#type_of_dept").bind("change", function(attrs) {
                    var id = [parseInt($(this).val())]
                    emp_child = []
                    orgdiagram = null;
                    counter = 0;
                    m_timer = null;
                    fromValue = null;
                    fromChart = null;
                    toValue = null;
                    toChart = null;
                    items = {};
                    jQuery.ajaxSetup({
                        cache: false
                    });
                    var value = $(this).val()
                    if(value == 0){
                        id = []
                    }
                    self.dept_dataset.read_slice(['id', 'name']).then(function(records) {
                        self.dept_data = records;
                        self.renderElement(value)
                        ResizePlaceholder();
                        orgdiagram = SetupWidget(self.$(".contentpanel"), "contentpanel", id)
                    });
                    
                });
                
                self.$("#toogl_expand").bind('click', function(e) {
                    if (self.$("#toogl_expand").text().trim("") == _t('Expand')) {
                        self.$(".contentpanel").orgDiagram({
                            pageFitMode: primitives.common.PageFitMode.None,
                        });
                        self.$(".contentpanel").orgDiagram("update", primitives.orgdiagram.UpdateMode.Refresh);
                        self.$("#toogl_expand").text("Shrink")
                    } else if (self.$("#toogl_expand").text().trim("") == _t('Shrink')) {
                        self.$(".contentpanel").orgDiagram({
                            pageFitMode: primitives.common.PageFitMode.pageHeight
                        });
                        self.$(".contentpanel").orgDiagram("update", primitives.orgdiagram.UpdateMode.Refresh);
                        self.$("#toogl_expand").text("Expand")
                    }
                    ResizePlaceholder()
                });
                var result;
                var options = new primitives.orgdiagram.Config();
                var itemsToAdd = [];
                var dept_ids = []
                self.dept_dataset.call('employee_dept', [[],id]).done(function(callbacks) {
                    var options = new primitives.orgdiagram.Config();
                    _.each(callbacks[0], function(employee) {
                        var employee_id = employee.emp_id
                        var employee_name = employee.emp_name
                        var employee_parent = parseInt(employee.parent)
                        var employee_email = employee.emp_email
                        var employee_job_title = employee.emp_job_title
                        var src = self.session.url('/web/binary/image', {
                            model: 'hr.employee',
                            field: 'image_medium',
                            id: employee_id
                        });
                        var employee_data = {
                                'id': employee_id,
                                'title': employee_name,
                                'parent': employee_parent,
                                'itemTitleColor': 'green',
                                'email': employee_email ? employee_email : '',
                                 childrenPlacementType: primitives.common.ChildrenPlacementType.Vertical,
                                 hasSelectorCheckbox: primitives.common.Enabled.False,
                                 'image': src,
                                 'description': employee_job_title ? employee_job_title : "",
                        }
                        itemsToAdd.push(employee_data)
                        items[employee_data.id] = employee_data
                    })
                    
                    _.each(callbacks[1], function(department) {
                        var emp_id = department.dept_employee_id;
                        var dept_id;
                        var dept_name = department.dept_name;
                        var dept_parent_id;
                        var dept_employee_id = department.dept_employee_id;
                        var dept_employee_name = department.dept_employee_name;
                        var dept_employee_email = department.dept_employee_email;
                        var dept_employee_job_title = department.dept_employee_job_title;
                        
                        if (department.dept_id.split("_")[1] != 'False') {
                            dept_id = department.dept_id
                        } else {
                            dept_id = null
                        }
                        if (department.dept_parent_id.split("_")[1] != 'False') {
                            dept_parent_id = department.dept_parent_id
                        } else {
                            dept_parent_id = null
                        }
                        var department_data = {
                                'id': dept_id,
                                'title': dept_name,
                                'parent': dept_parent_id,
                                'image': 'web_org_chart/static/src/img/dept.gif',
                                hasSelectorCheckbox: primitives.common.Enabled.True,
                                "itemTitleColor": "red",
                                'description': "",
                        }
                        dept_ids.push(dept_id)
                        var employee = {}
                        if (dept_employee_id) {
                            var src = self.session.url('/web/binary/image', {
                                model: 'hr.employee',
                                field: 'image_medium',
                                id: dept_employee_id
                            });
                            employee = {
                                    'id': dept_employee_id,
                                    'title': dept_employee_name,
                                    'parent': dept_id,
                                    'description': dept_employee_job_title,
                                    "itemTitleColor": "green",
                                    "email": dept_employee_email ? dept_employee_email : "",
                                    childrenPlacementType: primitives.common.ChildrenPlacementType.Vertical,
                                    hasSelectorCheckbox: primitives.common.Enabled.False,
                                    'image': src
                            }
                            itemsToAdd.push(employee)
                            items[employee.id] = employee
                        }
                        itemsToAdd.push(department_data)
                        items[department_data.id] = department_data
                    })
                    options.items = itemsToAdd;
                    options.cursorItem = 0;
                    options.selectedItems = dept_ids
                    options.pageFitMode = primitives.common.PageFitMode.pageHeight;
                    options.orientationType = primitives.common.OrientationType.Top;
                    options.horizontalAlignmentType = primitives.common.HorizontalAlignmentType.Center;
                    options.visibility = primitives.common.Visibility.Dot;
                    options.selectionPathMode = primitives.orgdiagram.SelectionPathMode.None,
                    options.items = itemsToAdd;
                    options.normalLevelShift = 20;
                    options.dotLevelShift = 10;
                    options.lineLevelShift = 10;
                    options.normalItemsInterval = 20;
                    options.dotItemsInterval = 10;
                    options.lineItemsInterval = 25;
                    options.templates = [getContactTemplate(), getZoom0Template(), getZoom1Template(), getZoom2Template(), getZoom3Template(), getZoom4Template()];
                    options.defaultTemplateName = "Zoom2";
                    options.onItemRender = (name == "contentpanel") ? onOrgDiagramTemplateRender : onOrgDiagramTemplateRender;
                    
                    /* chart uses mouse drag to pan items, disable it in order to avoid conflict with drag & drop */
                    options.enablePanning = false;
                    
                    result = element.orgDiagram(options);
                    $("#slider").slider({
                        value: 2,
                        min: 0,
                        max: 4,
                        step: 1,
                        slide: function(event, ui) {
                            self.$(".contentpanel").orgDiagram({
                                defaultTemplateName: "Zoom" + ui.value
                            });
                            self.$(".contentpanel").orgDiagram("update", primitives.orgdiagram.UpdateMode.Refresh);
                        }
                    });
                    element.find('.bt-item-frame').off( "click" );
                    element.on('click', '.bt-item-frame',function() {
                        var ids = $(this).attr('data-value')
                        if (ids.search('dept') != -1) {
                            var model_obj = new Model('hr.department');
                            model_obj.call('get_formview_id', [parseInt(ids.split('_')[1])]).then(function(view_id){
                                var pop = new common.FormViewDialog(self, {
                                    res_model:  'hr.department',
                                    res_id: parseInt(ids.split('_')[1]),
                                    title:_t("Open: Deparment"),
                                    view_id: view_id,
                                }).open();
                            });
                        } else {
                            var model_obj = new Model('hr.employee');
                            model_obj.call('get_formview_id', [ parseInt(ids)]).then(function(view_id){
                                var pop = new common.FormViewDialog(self, {
                                    res_model:  'hr.employee',
                                    res_id:  parseInt(ids),
                                    title:_t("Open: Employee"),
                                    view_id: view_id,
                                }).open();
                            });
                        }
                    });
                    element.droppable({
                        greedy: true,
                        drop: function(event, ui) {
                            /* Check drop event cancelation flag
                             * This fixes following issues:
                             * 1. The same event can be received again by updated chart
                             * so you changed hierarchy, updated chart and at the same drop position absolutly 
                             * irrelevant item receives again drop event, so in order to avoid this use primitives.common.stopPropagation
                             * 2. This particlular example has nested drop zones, in order to 
                             * suppress drop event processing by nested droppable and its parent we have to set "greedy" to false,
                             * but it does not work.
                             * In this example items can be droped to other items (except immidiate children in order to avoid looping)
                             * and to any free space in order to make them rooted.
                             * So we need to cancel drop  event in order to avoid double reparenting operation.
                             */
                            if (!event.cancelBubble) {
                                toValue = null;
                                toChart = name;
                                Reparent(fromChart, fromValue, toChart, toValue);
                                primitives.common.stopPropagation(event);
                            }
                        }
                    });
                    return result;
                });
            }

            function getZoom0Template() {
                var result = new primitives.orgdiagram.TemplateConfig();
                result.name = "Zoom0";
                result.itemSize = new primitives.common.Size(100, 10);
                result.minimizedItemSize = new primitives.common.Size(3, 3);
                result.highlightPadding = new primitives.common.Thickness(2, 2, 2, 2);
                var itemTemplate = jQuery(
                    '<div class="bp-item bp-corner-all bt-item-frame zoom0">' 
                        + '<div name="title" class="bp-item" style="top: 0px; left: 0px; width: 100px; height: 10px; font-size: 8px; text-align:center;"></div>'
                   + '</div>'
                ).css({
                    width: result.itemSize.width + "px",
                    height: result.itemSize.height + "px"
                }).addClass("bp-item");
                result.itemTemplate = itemTemplate.wrap('<div>').parent().html();
                return result;
            }

            function getZoom1Template() {
                var result = new primitives.orgdiagram.TemplateConfig();
                result.name = "Zoom1";
                result.itemSize = new primitives.common.Size(120, 28);
                result.minimizedItemSize = new primitives.common.Size(3, 3);
                result.highlightPadding = new primitives.common.Thickness(2, 2, 2, 2);
                var itemTemplate = jQuery(
                        '<div name="titleBackground" class="bp-item bp-corner-all bt-item-frame zoom1"  >' 
                            + '<div name="title" class="bp-item" style="top: 0px; left: 0px; width: 120px; height: 12px; font-size: 10px; text-align:center;"></div>' 
                       + '</div>'
                ).css({
                    width: result.itemSize.width + "px",
                    height: result.itemSize.height + "px"
                }).addClass("bp-item");
                result.itemTemplate = itemTemplate.wrap('<div>').parent().html();
                return result;
            }

            function getZoom2Template() {
                var result = new primitives.orgdiagram.TemplateConfig();
                result.name = "Zoom2";
                result.itemSize = new primitives.common.Size(140, 64);
                result.minimizedItemSize = new primitives.common.Size(3, 3);
                result.highlightPadding = new primitives.common.Thickness(2, 2, 2, 2);
                var itemTemplate = jQuery(
                        '<div class="bp-item bp-corner-all bt-item-frame" style="border-width: 1px;" >'
                        + '<div name="titleBackground" class="bp-item bp-corner-all bp-title-frame" style="top: 2px;width: 140px; height: 20px;">'
                            + '<img name="photo" style="height: 20px; width:43px;float:right;background: white" />'
                            + '<div name="title" class="bp-item" style="float:left;top: 2px; width: 84px; height: 12px; font-size: 10px; overflow: hidden;"></div>' 
                        + '</div>' 
                        + '<div class="bp-item"style="top: 24px;  height: 12px; font-size: 10px; overflow: hidden;margin-left: 5px;"><a name="email" href="" target="_top"></a></div>' 
                       + '<div name="description" class="bp-item" style="top: 38px; width: 84px; height: 62px; font-size: 10px; overflow: hidden;margin-left: 5px;"></div>' + '</div>'
                ).css({
                    width: result.itemSize.width + "px",
                    height: result.itemSize.height + "px"
                }).addClass("bp-item");
                result.itemTemplate = itemTemplate.wrap('<div>').parent().html();
                return result;
            }

            function getZoom3Template() {
                var result = new primitives.orgdiagram.TemplateConfig();
                result.name = "Zoom3";
                result.itemSize = new primitives.common.Size(200, 100);
                result.minimizedItemSize = new primitives.common.Size(4, 4);
                result.highlightPadding = new primitives.common.Thickness(2, 2, 2, 2);
                var itemTemplate = jQuery(
                        '<div class="bp-item bp-corner-all bt-item-frame" style="border-width: 1px; width: 95px; height: 99px;  left: 922.5px; position: absolute; padding: 0px; margin: 0px; visibility: inherit;">'
                        + '<div name="titleBackground" class="bp-item bp-corner-all bp-title-frame" style="top: 2px; left: 2px; width: 216px; height: 20px;">' 
                            + '<img name="photo" style="height: 20px; width:43px;float:right;margin-right:19px;background: white" />'
                            + '<div name="title" class="bp-item bp-title" style="top: 3px; left: 6px; width: 208px; height: 18px;">' 
                            + '</div>' 
                        + '</div>' 
                        + '<div name="description" class="bp-item" style="top: 62px;width: 162px; height: 36px; font-size: 12px;margin-left: 5px;"></div>' 
                        + '<div class="bp-item" style="top: 44px; width: 162px; height: 18px; font-size: 12px;margin-left: 5px;"><a name="email" href="" target="_top"></a></div>' + '</div>'
                ).css({
                    width: result.itemSize.width + "px",
                    height: result.itemSize.height + "px"
                }).addClass("bp-item bp-corner-all bt-item-frame");
                result.itemTemplate = itemTemplate.wrap('<div>').parent().html();
                return result;
            }

            function getZoom4Template() {
                var result = new primitives.orgdiagram.TemplateConfig();
                result.name = "Zoom4";
                result.itemSize = new primitives.common.Size(220, 120);
                result.minimizedItemSize = new primitives.common.Size(3, 3);
                result.highlightPadding = new primitives.common.Thickness(2, 2, 2, 2);
                var itemTemplate = jQuery(
                        '<div class="bp-item bp-corner-all bt-item-frame" style="border-width: 1px; width: 95px; height: 99px;  left: 922.5px; position: absolute; padding: 0px; margin: 0px; visibility: inherit;">' 
                            + '<div name="titleBackground" class="bp-item bp-corner-all bp-title-frame" style="top: 2px; left: 2px; width: 216px; height: 20px;">' 
                                + '<img name="photo" style="height: 20px; width:43px;float:right;background: white" />'
                                + '<div name="title" class="bp-item bp-title" style="top: 3px; left: 6px; width: 208px; height: 18px;">' + '</div>' 
                            + '</div>' 
                            + '<div name="description" class="bp-item" style="top: 62px;width: 162px; height: 36px; font-size: 12px;margin-left: 5px;"></div>' 
                            + '<div class="bp-item" style="top: 44px;width: 162px; height: 18px; font-size: 12px;margin-left: 5px;"><a name="email" href="" target="_top"></a></div>' 
                        + '</div>'
                ).css({
                    width: result.itemSize.width + "px",
                    height: result.itemSize.height + "px"
                }).addClass("bp-item bp-corner-all bt-item-frame");
                result.itemTemplate = itemTemplate.wrap('<div>').parent().html();
                return result;
            }

            function getContactTemplate() {
                var result = new primitives.orgdiagram.TemplateConfig();
                result.name = "contactTemplate";
                result.itemSize = new primitives.common.Size(200, 100);
                result.minimizedItemSize = new primitives.common.Size(4, 4);
                result.highlightPadding = new primitives.common.Thickness(2, 2, 2, 2);
                var itemTemplate = jQuery(
                        '<div class="bp-item bp-corner-all bt-item-frame" style="border-width: 1px; width: 95px; height: 99px;  left: 922.5px; position: absolute; padding: 0px; margin: 0px; visibility: inherit;">' + '<div name="titleBackground" class="bp-item bp-corner-all bp-title-frame" style="top: 2px; left: 2px; width: 216px; height: 20px;">' + '<img name="photo" style="height: 20px; width:43px;float:right;margin-right:19px;background: white" />'
                        + '<div name="title" class="bp-item bp-title" style="top: 3px; left: 6px; width: 208px; height: 18px;">' + '</div>' + '</div>' + '<div name="description" class="bp-item" style="top: 62px; left: 56px; width: 162px; height: 36px; font-size: 12px;"></div>' + '<div class="bp-item" style="top: 44px; left: 56px; width: 162px; height: 18px; font-size: 12px;"><a name="email" href="" target="_top"></a></div>' + '</div>'
                ).css({
                    width: result.itemSize.width + "px",
                    height: result.itemSize.height + "px"
                }).addClass("bp-item bp-corner-all bt-item-frame");
                result.itemTemplate = itemTemplate.wrap('<div>').parent().html();
                return result;
            }

            function onOrgDiagramTemplateRender(event, data) {
                switch (data.renderingMode) {
                    case primitives.common.RenderingMode.Create:
                        data.element.draggable({
                            revert: "invalid",
                            containment: ".contentpanel",
                            scroll: true,
                            appendTo: ".o_content",
                            helper: function() {
                                var $copy = $(this).clone();
                                return $copy;
                            },
                            cursor: "move",
                            "zIndex": 10,
                            delay: 30,
                            distance: 10,
                            start: function(event, ui) {
                                ResizePlaceholder()
                                fromValue = jQuery(this).attr("data-value");
                                fromChart = "contentpanel";
                            },
                            drag: function(event, ui) {
                                // Keep the left edge of the element
                                // at least 100 pixels from the container
                                ui.position.left = Math.min(ui.position.left, self.$(".contentpanel").width() - 200);
                                ui.position.top = Math.min(ui.position.top, self.$(".contentpanel").height() - 50);
                            },
                        });
                        data.element.droppable({
                            /* this option is supposed to suppress event propogation from nested droppable to its parent
                             *  but it does not work*/
                            greedy: true,
                            drop: function(event, ui) {
                                if (!event.cancelBubble) {
                                    toValue = jQuery(this).attr("data-value");
                                    toChart = "contentpanel";
                                    Reparent(fromChart, fromValue, toChart, toValue);
                                    primitives.common.stopPropagation(event);
                                } else {
                                    console.log("Drop ignored!");
                                }
                            },
                            over: function(event, ui) {
                                toValue = jQuery(this).attr("data-value");
                                toChart = "contentpanel";
                                $(".o_content").animate({
                                    scrollTop: event.target.offsetTop,
                                    scrollLeft: event.target.offsetLeft - 400
                                });
                                jQuery(this).attr("data-value")
                                    /* this is needed in order to update highlighted item in chart, 
                                 * so this creates consistent mouse over feed back */
                                self.$(".contentpanel").orgDiagram({
                                    "highlightItem": toValue
                                });
                                self.$(".contentpanel").orgDiagram("update", primitives.common.UpdateMode.PositonHighlight);
                            },
                            accept: function(draggable) {
                                /* be carefull with this event it is called for every available droppable including invisible items on every drag start event.
                                 * don't varify parent child relationship between draggable & droppable here it is too expensive.*/
                                return (jQuery(this).css("visibility") == "visible");
                            }
                        });
                        /* Initialize widgets here */
                        break;
                    case primitives.common.RenderingMode.Update:
                        /* Update widgets here */
                        break;
                }
                var itemConfig = data.context;
                /* Set item id as custom data attribute here */
                data.element.attr("data-value", itemConfig.id);
                RenderField(data, itemConfig);
            }

            function Reparent(fromChart, value, toChart, toParent) {
                /* following verification needed in order to avoid conflict with jQuery Layout widget */
                if (fromChart != null && value != null && toChart != null) {
                    var item = items[value];
                    var fromItems = jQuery("#" + fromChart).orgDiagram("option", "items");
                    var toItems = jQuery("#" + toChart).orgDiagram("option", "items");
                    if (toParent != null) {
                        var toParentItem = items[toParent];
                        var to_id;
//                        this.org_dataset = new data.DataSetSearch(this, 'hr.department', {}, []);
                        var org_dataset = new data.DataSetSearch(this, 'hr.department', {}, []);
                        if (typeof toParentItem.id == "number") {
                            to_id = parseInt(toParentItem.id);
                        } else {
                            to_id = parseInt(toParentItem.id.split('_')[1])
                        }
//                        this.org_dataset.read_slice(['id', 'manager_id'], {
                        org_dataset.read_slice(['id', 'manager_id'], {
                            'domain': [
                                       ['id', '=', to_id]
                             ]
                        }).then(function(table_records) {
                            if (typeof item.id == "string" && typeof toParentItem.id == "number") {
                                alert("Not Possible")
                                return false
                            } else if (typeof item.id == "string" || (typeof item.id == "number" && typeof toParentItem.id == "number")) {
                                if (!isParentOf(item, toParentItem)) {
                                    var children = getChildrenForParent(item);
                                    children.push(item);
                                    for (var index = 0; index < children.length; index++) {
                                        var child = children[index];
                                        fromItems.splice(primitives.common.indexOf(fromItems, child), 1);
                                        toItems.push(child);
                                    }
                                    item.parent = toParent;
                                }
                                self.$(".contentpanel").orgDiagram("update", primitives.common.UpdateMode.Recreate);
                            } else if (table_records[0].manager_id) {
                                alert("Manager Already Exists..")
                                return false
                            } else {
                                if (!isParentOf(item, toParentItem)) {
                                    var children = getChildrenForParent(item);
                                    children.push(item);
                                    for (var index = 0; index < children.length; index++) {
                                        var child = children[index];
                                        fromItems.splice(primitives.common.indexOf(fromItems, child), 1);
                                        toItems.push(child);
                                    }
                                    item.parent = toParent;
                                }
                                self.$(".contentpanel").orgDiagram("update", primitives.common.UpdateMode.Recreate);
                            }
                        });
                    }
                }
            }

            function getChildrenForParent(parentItem) {
                var children = {};
                for (var id in items) {
                    var item = items[id];
                    if (children[item.parent] == null) {
                        children[item.parent] = [];
                    }
                    children[item.parent].push(id);
                }
                var newChildren = children[parentItem.id];
                var result = [];
                if (newChildren != null) {
                    while (newChildren.length > 0) {
                        var tempChildren = [];
                        for (var index = 0; index < newChildren.length; index++) {
                            var item = items[newChildren[index]];
                            result.push(item);
                            if (children[item.id] != null) {
                                tempChildren = tempChildren.concat(children[item.id]);
                            }
                        }
                        newChildren = tempChildren;
                    }
                }
                return result;
            }

            function isParentOf(parentItem, childItem) {
                var self = this;
                self.org_dataset = new data.DataSetSearch(self, 'hr.department', {}, []);
                self.org_emp_dataset = new data.DataSetSearch(self, 'hr.employee', {}, []);
                //dtod
                if (typeof parentItem.id == "string" && typeof childItem.id == "string") {
                    self.org_dataset.write(parseInt(parentItem.id.split("_")[1]), {
                        'parent_id': parseInt(childItem.id.split("_")[1])
                    });
                }
                //etod
                if (typeof parentItem.id == "number" && typeof childItem.id == "string") {
                    var parentItem_parent = parentItem.parent
                    var parentItem_id = parentItem.id
                    self.org_dataset.write(parseInt(childItem.id.split("_")[1]), {
                        'manager_id': parseInt(parentItem.id)
                    }).done(function() {
                        if (typeof parentItem_parent == "number") {
                            self.org_emp_dataset.write(parentItem_id, {
                                'parent_id': false
                            });
                        } else {
                            self.org_dataset.write(parseInt(parentItem_parent.split("_")[1]), {
                                'manager_id': false
                            });
                        }
                    });
                }
                //etoe
                if (typeof parentItem.id == "number" && typeof childItem.id == "number") {
                    var parentItem_parent = parentItem.parent
                    self.org_emp_dataset.write(parseInt(parentItem.id), {
                        'parent_id': parseInt(childItem.id)
                    }).done(function() {
                        if (typeof parentItem_parent == "string") {
                            self.org_dataset.write(parseInt(parentItem_parent.split("_")[1]), {
                                'manager_id': false
                            });
                        }
                    });
                    //this.org_emp_dataset.write(parseInt(childItem.id),{'parent_id':false});
                }
                var result = false,
                    index,
                    len,
                    itemConfig;
                if (parentItem.id == childItem.id) {
                    result = true;
                } else {
                    while (childItem.parent != null) {
                        childItem = items[childItem.parent];
                        if (childItem.id == parentItem.id) {
                            result = true;
                            break;
                        }
                    }
                }
                return result;
            };

            function RenderField(data, itemConfig) {
                //if (data.templateName == "contactTemplate") {
                data.element.find("[name=photo]").attr({
                    "src": itemConfig.image,
                    "alt": itemConfig.title
                });
                data.element.find("[name=titleBackground]").css({
                    "background": itemConfig.itemTitleColor
                });
                data.element.find("[name=email]").attr({
                    "href": ("mailto:" + itemConfig.email + "?Subject=Hello%20again")
                });
                var fields = ["title", "description", "phone", "email"];
                for (var index = 0; index < fields.length; index++) {
                    var field = fields[index];
                    var element = data.element.find("[name=" + field + "]");
                    if (element.text() != itemConfig[field]) {
                        element.text(itemConfig[field]);
                    }
                }
            // }
            }

            jQuery(window).resize(function() {
                ResizePlaceholder()
            })

            function ResizePlaceholder() {
                var panel = jQuery("window");
                var panelSize = new primitives.common.Rect(0, 0, panel.innerWidth(), panel.innerHeight());
                var position = new primitives.common.Rect(0, 0, panelSize.width / 2, panelSize.height);
                position.offset(-2);
                var position2 = new primitives.common.Rect(panelSize.width / 2, 0, panelSize.width / 2, panelSize.height);
                position2.offset(-2);
                self.$(".contentpanel").css(position.getCSS());
                var bodyWidth = $(window).width()
                var bodyHeight = $(window).height() - 80
                if (jQuery(".placeholder.orgdiagram").height()) {
                    bodyHeight = jQuery(".placeholder.orgdiagram").height();
                    bodyWidth = jQuery(".placeholder.orgdiagram").width();
                }
                self.$(".contentpanel").css({
                    "width": bodyWidth + "px",
                    "height": bodyHeight + "px",
                });
                self.$(".contentpanel").addClass("set_style")
            }
        }

    })
    
    common.FormViewDialog.include({
        init: function(parent, options) {
            var self = this;

            var multi_select = !_.isNumber(options.res_id) && !options.disable_multiple_selection;
            var readonly = _.isNumber(options.res_id) && options.readonly;

            if(!options || !options.buttons) {
                options = options || {};
                options.buttons = [
                    {text: (readonly ? _t("Close") : _t("Discard")), classes: "btn-default o_form_button_cancel", close: true, click: function() {
                        self.view_form.trigger('on_button_cancel');
                    }}
                ];

                if(!readonly) {
                    options.buttons.splice(0, 0, {text: _t("Save") + ((multi_select)? _t(" & Close") : ""), classes: "btn-primary o_formdialog_save", click: function() { // o_formdialog_save class for web_tests!
                            $.when(self.view_form.save()).done(function() {
                                self.view_form.reload_mutex.exec(function() {
                                    if(self.options && (self.options.title == _t('Open: Employee') || self.options.title == _t('Open: Deparment'))){
                                        $("#type_of_dept").change();
                                    }
                                    self.trigger('record_saved');
                                    self.close();
                                });
                            });
                        }
                    });

                    if(multi_select) {
                        options.buttons.splice(1, 0, {text: _t("Save & New"), classes: "btn-primary", click: function() {
                            $.when(self.view_form.save()).done(function() {
                                self.view_form.reload_mutex.exec(function() {
                                    self.view_form.on_button_new();
                                });
                            });
                        }});
                    }
                }
            }
            this._super(parent, options);
        },
    });
    core.action_registry.add('orgchart.company_employee',org_chart_company_employee);

});
