// admin_dashboard.js — seller decline confirmation with a prompt for the rejection reason

// ==============================================================================
// SECTION: Seller Decline Confirmation
// ==============================================================================

function confirmDecline(form) {
  var reason = prompt('Enter reason for declining this seller request:');
  if (reason === null) return false;
  form.querySelector('.rejection-reason').value = reason || 'No reason provided';
  return true;
}
