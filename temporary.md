*This will serve as temporary guide to building my project.
I am building this procedurally, trying to avoid most in-built modules
and opting for low level libraries and abstracts
where possible.

## Current progress-
I have finished setting up basic configurations for the Django application.
I am now going to configure the application to serve as backend for a cloud-based ERM solution service.

### TO-DO LIST
* Configure a custom user model instead of using Django's `Model` utility
* Define basic API views:
    * registration
    * login
    * logout
    * other views will be added as seen fit
* JWT-based authentication
* Email verification
  * Configure email backend
  * Generate token+link on registration
  * Confirm via view when link is visited
* Permissions and Middleware
  * Add authentication classes to configurations
  * Add permission classes (eg. IsAuthenticated)
  * Secure endpoints