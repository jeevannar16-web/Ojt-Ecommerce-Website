function confirmDecline(form) {
  var reason = prompt('Enter reason for declining this seller request:');
  if (reason === null) return false;
  form.querySelector('.rejection-reason').value = reason || 'No reason provided';
  return true;
}
