$(function() {
  var PAINT_MODE = 1;
  var CONTOUR_MODE = 2;
  var isDrawing = false;
  var mode = PAINT_MODE;
  var startPoint = null;
  var endPoint = null;
  var circles = [];
  var contours = [];
  var subImage = null;
  var canvas = $('#canvas');
  var image = $('#image');
  canvas[0].width = image.width();
  canvas[0].height = image.height();
  var context = canvas[0].getContext('2d');
  var icons = $('.icon-span');
  var paint = $('#paint');
  var contour = $('#contour');
  var eraser = $('#eraser');
  var action = $('#action');
  var offset = canvas.offset();

  function getMousePosition(e) {
    var x = e.pageX - offset.left,
        y = e.pageY - offset.top;
    return { x: x, y: y };
  };

  function drawCircle(x, y, radius) {
    context.beginPath();
    context.arc(x, y, radius, 0, 2 * Math.PI, false);
    context.fillStyle = '#FFFFFF';
    context.fill();
  };

  function drawRect(x, y, width, height) {
    context.beginPath();
    context.rect(x, y, width, height);
    context.fillStyle = '#FF0000';
    context.fill();
  };

  function drawOutlineRect(point1, point2) {
    var width = point2.x - point1.x;
    var height = point2.y - point1.y;
    context.beginPath();
    context.rect(point1.x, point1.y, width, height);
    context.strokeStyle = '#000000';
    context.stroke();
  };

  function redraw() {
    context.clearRect(0, 0, image.width(), image.height());
    for (var i in contours) {
      contour = contours[i];
      context.putImageData(contour.image, contour.x, contour.y);
    }
    for (var i in circles) {
      var point = circles[i];
      drawCircle(point.x, point.y, 30);
    }
    if (startPoint != null && endPoint != null) {
      drawOutlineRect(startPoint, endPoint);
    }
  }

  function getContours(point1, point2) {
    if (point2.x < point1.x) {
        temp = point2.x;
        point2.x = point1.x;
        point1.x = temp;
    }
    if (point2.y < point1.y) {
        temp = point2.y;
        point2.y = point1.y;
        point1.y = temp; 
    } 
    var width = point2.x - point1.x;
    var height = point2.y - point1.y;
    if (width == 0 || height == 0) {
        return;
    }
    var scaleContext = document.createElement("canvas").getContext("2d");
    scaleContext.canvas.width = image.width();
    scaleContext.canvas.height = image.height();
    scaleContext.drawImage(image[0], 0, 0, image.width(), image.height());
    var cropContext = document.createElement("canvas").getContext("2d");
    cropContext.canvas.width = width;
    cropContext.canvas.height = height;
    cropContext.drawImage(scaleContext.canvas, point1.x, point1.y, width, height, 0, 0, width, height);
    var cropImage = cropContext.getImageData(0, 0, width, height);
    var threshImage = Filters.filterImage(Filters.threshold_average, cropImage, true);
    var floodImage = Filters.filterImage(Filters.floodfill, threshImage, 0, 0, {r: 255, g: 255, b: 255, a: 255}); 
    var inverseImage = Filters.filterImage(Filters.inverse, floodImage);
    var filledImage = Filters.filterImage(Filters.combine, threshImage, inverseImage);
    contours.push({x: point1.x, y: point1.y, image: filledImage});
  }

  icons.tooltip();
  paint.click(function() {
    mode = PAINT_MODE;
  });
  contour.click(function() {
    mode = CONTOUR_MODE;
  });
  eraser.click(function() {
    circles = [];
    contours = [];
    redraw();
  });
  action.click(function() {
    $('#data').val(canvas[0].toDataURL('image/png'));
    $('#form').submit();
  });
  canvas.mousedown(function(e) {
    isDrawing = true;
    var point = getMousePosition(e);
    if (mode == PAINT_MODE) {
      circles.push(point);
    } else if (mode == CONTOUR_MODE) {
      startPoint = point;
      endPoint = point;
    }
    redraw();
  });
  canvas.mousemove(function(e) {
    if (isDrawing) {
      var point = getMousePosition(e);
      if (mode == PAINT_MODE) {
        circles.push(point);
      } else if (mode == CONTOUR_MODE) {
        endPoint = point;
      }
      redraw();
    }
  });
  canvas.mouseup(function(e) {
    isDrawing = false;
    if (mode == CONTOUR_MODE) {
      getContours(startPoint, endPoint);
      startPoint = null;
      endPoint = null;
    }
    redraw();
  });
});
