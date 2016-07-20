$(function() {
  var icons = $('.icon-span');
  var submit = $('#submit');
  var upload = $('#upload');
  icons.tooltip();
  upload.click(function() {
    submit.click();
  });
});
