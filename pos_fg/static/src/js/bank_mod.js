console.log('in bank payment method mod');
odoo.define('cash',function(require){
    "use strict";
    let PaymentScreen = require('point_of_sale.PaymentScreen');
    const originalAddNewPaymentLine = PaymentScreen.prototype.addNewPaymentLine;
    PaymentScreen.prototype.addNewPaymentLine = function ({ detail: paymentMethod }) {
        if (paymentMethod.name == 'Credit Card'||paymentMethod.name == 'M-Pesa' ) {
           let auth_code_input = document.querySelector('input[name="auth_code"]');
           auth_code_input.disabled = false;
           auth_code_input.style.backgroundColor = "white";
        }
        originalAddNewPaymentLine.apply(this,arguments);
    };


})
