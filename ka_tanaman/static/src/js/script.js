/* custom js script untuk ka_tanaman */

var color = {
	notvalid: {
		warna: 'merah',
		code: '#ff0000',
		icon: 'ka_tanaman/static/src/img/marker1.png'
	},
	belumtebang: {
		warna: 'biru',
		code: '#0099ff',
		icon: 'ka_tanaman/static/src/img/marker2.png'
	},
	masihtebang: {
		warna: 'oranye',
		code: '#ff9933',
		icon: 'ka_tanaman/static/src/img/marker3.png'
	},
	sudahtebang: {
		warna: 'hijau',
		code: '#66ff66',
		icon: 'ka_tanaman/static/src/img/marker4.png'
	},
	intersect: {
		warna: 'hitam',
		code: '#000000',
	},
	search: {
		icon: 'ka_tanaman/static/src/img/marker_search.png',
	},
	rehab: {
		icon: 'ka_tanaman/static/src/img/rehab.png'
	}
}

var map = {
	api_key: 'AIzaSyCXlneV0k7BokJMJqoL344j_vWbah6Ia4k',
	status: false,
};

var mapRehab = null;
var isGmapLoaded = false;
initGmap = function() {
	isGmapLoaded = true;
}

class GmapHelpers {
	constructor() {
		this.gmap = null;
		this.searchMarker = null;
		this.zoomSearchLevel = 17;
		this.polygonDraw = null;
		this.polygonEdit = null;
	}

	init() {
		var src = '<script src="https://maps.googleapis.com/maps/api/js?key=' + map.api_key + '&amp;libraries=drawing&amp;callback=initGmap" async defer></script>';
		$('body').append(src);
	}

	createMap(container, centerLatitude, centerLongitude, zoom) {
		this.gmap = new google.maps.Map(container, {
			center: {lat: centerLatitude, lng: centerLongitude},
			zoom: zoom,
			mapTypeId: google.maps.MapTypeId.HYBRID,
		});
	}

	createMarker(latitude, longitude, iconPath) {
		return new google.maps.Marker({
			map: this.gmap,
			position: {lat: latitude, lng: longitude},
			icon: iconPath,
		});
	}

	createSearchMarker(latitude, longitude, iconPath) {
		if (this.searchMarker != null) {
			this.searchMarker.setMap(null);
			this.searchMarker = null;
		}
		
		this.searchMarker = this.createMarker(latitude, longitude, iconPath);
		this.gmap.setCenter(new google.maps.LatLng(latitude, longitude));
		this.gmap.setZoom(17);
	}

	createRehabMarker(latitude, longitude, iconPath, dataInfoWindowString) {
		dataInfoWindowString = dataInfoWindowString || null;

		var self = this;
		var marker = this.createMarker(latitude, longitude, iconPath);
		if (dataInfoWindowString != null) {
			var infoWindow = new google.maps.InfoWindow;
			marker.addListener('click', function(event) {
				infoWindow.setContent(dataInfoWindowString);
				infoWindow.setPosition(event.latLng);
				infoWindow.open(self.gmap);
			});
		}
	}

	createPolygon(objPolygon, color, dataInfoWindowString, isEditable) {
		if (typeof objPolygon === 'undefined' || typeof color === 'undefined' || !objPolygon.length || !color) return;
		
		dataInfoWindowString = dataInfoWindowString || null;
		isEditable = isEditable || false;

		var polygon = new google.maps.Polygon({
			paths: objPolygon,
			strokeColor: color,
			strokeOpacity: 0.8,
			strokeWeight: 2,
			fillColor: color,
			fillOpacity: 0.4,
			editable: isEditable,
		});

		polygon.setMap(this.gmap);

		var self = this;
		if (dataInfoWindowString != null) {
			var infoWindow = new google.maps.InfoWindow;
			polygon.addListener('click', function(event) {
				infoWindow.setContent(dataInfoWindowString);
				infoWindow.setPosition(event.latLng);
				infoWindow.open(self.gmap);
			});
			
		}

		if (isEditable) {
			polygon.addListener('rightclick', function(event) {
				if (event.vertex == undefined) return;

				var delVertex = new DeleteVertexMenu();
				delVertex.open(self.gmap, polygon.getPath(), event.vertex);
			});

			self.polygonEdit = polygon;
		}
	}

	drawPolygon() {
		var self = this;

		var drawingManager = new google.maps.drawing.DrawingManager({
			drawingControl: true,
			drawingControlOptions: {
				position: google.maps.ControlPosition.TOP_CENTER,
				drawingModes: ['polygon']
			}
		});

		drawingManager.setMap(self.gmap);

		google.maps.event.addListener(drawingManager, 'polygoncomplete', function(polygon) {
			drawingManager.drawingControl = false;
			drawingManager.drawingMode = null;
			var path = polygon.getPath();
			self.polygonDraw = [];
			for (var i=0;i<path.length;i++) {
				var p = path.getAt(i);
				self.polygonDraw.push([p.lat(), p.lng()]);
			}
		});
	}

	resetPolygonDraw() {
		this.polygonDraw = null;
	}

	getPolygonEditValue() {
		if (this.polygonEdit == null) return null;
		
		var vertices = this.polygonEdit.getPath();
		var newPolygon = [];
		for (var i=0;i<vertices.getLength();i++) {
			var xy = vertices.getAt(i);
			newPolygon.push([xy.lat(), xy.lng()]);
		}

		return newPolygon;
	}

	static convertArrayToObject(coordinates) {
		var arrayOfObject = [];
		for (var i=0;i<coordinates.length;i++) {
			var c = coordinates[i];
			arrayOfObject.push(new google.maps.LatLng(c[0], c[1]));
		}

		return arrayOfObject;
	}

	static getCenterValue(coordinates) {
		var latitude = [];
		var longitude = [];

		for (var i=0;i<coordinates.length;i++) {
			var _c = coordinates[i];
			latitude.push(_c[0]);
			longitude.push(_c[1]);
		}

		latitude.sort(function(a, b) {return a-b});
		longitude.sort(function(a, b) {return a-b});

		var centerLat = (latitude[0] + latitude[latitude.length-1]) / 2;
		var centerLng = (longitude[0] + longitude[longitude.length-1]) / 2;

		return [centerLat, centerLng];
	}
}