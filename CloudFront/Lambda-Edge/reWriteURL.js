/* AWS Lambda@Edge
Trigger Type: Origin Request
Use Case: When S3 is set as origin and you want to serve the request for the URL '/about' instead of '/about/index.html'
*/

'use strict';

exports.handler = (event, context, callback) => {

    const request = event.Records[0].cf.request;
    const headers = request.headers;
    
    console.log(`Request uri before "${request.uri}"`);
    
    if (request.uri === '/about' || request.uri === '/contact') {
    
       request.uri=request.uri+"/index.html";
       console.log(`Request uri set to "${request.uri}"`);
       callback(null, request);
       return;
       
    }
    console.log(`Request uri set to "${request.uri}"`);
    callback(null, request);
    
};
