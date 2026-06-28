// ==============================================================================
// File: admin_dashboard.js
// Description: Seller decline confirmation with rejection reason prompt
// ==============================================================================

// ==============================================================================
// SECTION: Seller Decline Confirmation
// ==============================================================================

function confirmDecline(form) {
  var reason = prompt('Enter reason for declining this seller request:');
  if (reason === null) return false;
  form.querySelector('.rejection-reason').value = reason || 'No reason provided';
  return true;
}
