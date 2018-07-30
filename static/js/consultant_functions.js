// On document ready

$(function () {

    update_copyright_date_in_footer();
    // Attach change password submit button function
    $('#change_password_form').find('input[type=submit]').click(process_change_password);
})

function update_copyright_date_in_footer() {

    var d = new Date();
    $('#copyright_year').text(d.getFullYear());

}

function process_change_password(e) {
    e.preventDefault();
    console.log('submit attempted');
    var form_data = $('#change_password_form').serialize();

    if ($('[name=confirm_pass]').val() != $('[name=new_pass]').val()) {
        $('#change_password_form').prepend('<div id="confirm_password_error" class="alert alert-danger mx-4">Your new password and confirmed password do not match. Please try again.</div>');
        $('#confirm_pass').val('');
        $('#new_pass').val('');
        $('#confirm_pass').click(function () {
            $('#confirm_password_error').remove();
        })
        $('#new_pass').click(function () {
            $('#confirm_password_error').remove();
        })
    }

    else {

        $.ajax({
            url: '/api/consultants/' + $('[name=c_id]').val() + '/change_password',
            data: $('#change_password_form').serialize(),
            type: 'POST',
            success: function (response) {
                console.log(response);
                // reset change password form and hide modal
                $('#change_password_form').find('input[type=password]').val('');
                $('#cancel_change_password_button').trigger('click');

            },
            error: function (error) {
                console.log(error);
                $('#change_password_form').prepend('<div id="change_password_error" class="alert alert-danger mx-4">' + error.responseText + '</div>');
                $('#change_password_form').find('input').click(function(){
                    $('#change_password_error').remove();
                })
            }
        });
    }

}
