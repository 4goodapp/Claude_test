2. **Status Code** - HTTP status (200, 404, 500, etc.)
3. **Headers** - HTTP headers (Content-Type, Location, Cache-Control, etc.)

```java
ResponseEntity<User> response = ResponseEntity
    .status(HttpStatus.CREATED)                    // Status
        .header("X-Custom-Header", "myValue")         // Headers
	    .body(user);                                  // Body
	    ```

## Common Patterns

### 1. Success Cases

```java
// Simple 200 OK
return ResponseEntity.ok(data);

// 201 Created (typically for POST)
return ResponseEntity
    .created(URI.create("/api/users/" + user.getId()))
        .body(user);

// 204 No Content (successful but no data to return)
@DeleteMapping("/user/{id}")
public ResponseEntity<Void> deleteUser(@PathVariable Long id) {
    userService.delete(id);
        return ResponseEntity.noContent().build();
	}
	```

### 2. Error Cases

```java
// 404 Not Found
return ResponseEntity.notFound().build();

// 400 Bad Request
return ResponseEntity.badRequest().body(errorMessage);

// 500 Internal Server Error
return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
    .body(errorDetails);
    ```

### 3. Conditional Responses

```java
@GetMapping("/user/{id}")
public ResponseEntity<User> getUser(@PathVariable Long id) {
    return userService.findById(id)
            .map(ResponseEntity::ok)
	            .orElse(ResponseEntity.notFound().build());
		    }
		    ```

### 4. Custom Headers

```java
@GetMapping("/download/{fileId}")
public ResponseEntity<Resource> downloadFile(@PathVariable Long fileId) {
    Resource file = fileService.load(fileId);

    return ResponseEntity.ok()
            .header(HttpHeaders.CONTENT_DISPOSITION,
	                    "attachment; filename=\"" + file.getFilename() + "\"")
			            .contentType(MediaType.APPLICATION_OCTET_STREAM)
				            .body(file);
					    }

@GetMapping("/data")
public ResponseEntity<Data> getData() {
    return ResponseEntity.ok()
            .cacheControl(CacheControl.maxAge(1, TimeUnit.HOURS))
	            .body(data);
		    }
		    ```

### 5. Location Header Pattern (REST Best Practice)

When you create a resource, include its location:

```java
@PostMapping("/users")
public ResponseEntity<User> createUser(@RequestBody User user) {
    User saved = userService.save(user);

    URI location = ServletUriComponentsBuilder
            .fromCurrentRequest()
	            .path("/{id}")
		            .buildAndExpand(saved.getId())
			            .toUri();

    return ResponseEntity.created(location).body(saved);
    }
    ```

This returns:
```
HTTP/1.1 201 Created
Location: http://localhost:8080/users/123
Content-Type: application/json

{ "id": 123, "name": "John" }
```

## Builder vs. Constructor

Two ways to create `ResponseEntity`:

```java
// Builder style (more readable)
return ResponseEntity
    .status(HttpStatus.OK)
        .header("X-Custom", "value")
	    .body(data);

// Constructor style (more direct)
return new ResponseEntity<>(data, headers, HttpStatus.OK);
```

Use builders for readability, constructors when you have complex header manipulation.

## Generic Type `<T>`

The generic type tells Spring what you're returning:

```java
ResponseEntity<User>           // Single object
ResponseEntity<List<User>>     // List
ResponseEntity<Void>           // No body (for 204, 404, etc.)
ResponseEntity<?>              // Any type (avoid if possible)
```

## Real-World Example: CRUD Operations

```java
@RestController
@RequestMapping("/api/products")
public class ProductController {

    @GetMapping("/{id}")
        public ResponseEntity<Product> getProduct(@PathVariable Long id) {
	        return productService.findById(id)
		            .map(product -> ResponseEntity
			                    .ok()
					                    .eTag(String.valueOf(product.getVersion()))
							                    .body(product))
									                .orElse(ResponseEntity.notFound().build());
											    }

    @PostMapping
        public ResponseEntity<Product> createProduct(@Valid @RequestBody Product product) {
	        Product saved = productService.save(product);

        URI location = ServletUriComponentsBuilder
	            .fromCurrentRequest()
		                .path("/{id}")
				            .buildAndExpand(saved.getId())
					                .toUri();

        return ResponseEntity.created(location).body(saved);
	    }

    @PutMapping("/{id}")
        public ResponseEntity<Product> updateProduct(
	            @PathVariable Long id,
		                @RequestBody Product product) {

        if (!productService.exists(id)) {
	            return ResponseEntity.notFound().build();
		            }

        Product updated = productService.update(id, product);
	        return ResponseEntity.ok(updated);
		    }

    @DeleteMapping("/{id}")
        public ResponseEntity<Void> deleteProduct(@PathVariable Long id) {
	        if (!productService.exists(id)) {
		            return ResponseEntity.notFound().build();
			            }

        productService.delete(id);
	        return ResponseEntity.noContent().build();
		    }
		    }
		    ```

## When NOT to Use ResponseEntity

If you just need to return data with 200 OK, skip it:

```java
// Overkill
@GetMapping("/users")
public ResponseEntity<List<User>> getUsers() {
    return ResponseEntity.ok(userService.findAll());
    }

// Better
@GetMapping("/users")
public List<User> getUsers() {
    return userService.findAll();
    }
    ```

Use `ResponseEntity` when you need to control status codes, headers, or have conditional responses.

## Exception Handling Alternative

For error cases, `@ExceptionHandler` is often cleaner than littering your code with error ResponseEntity objects:

```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(UserNotFoundException.class)
        public ResponseEntity<ErrorDetails> handleUserNotFound(UserNotFoundException ex) {
	        ErrorDetails error = new ErrorDetails(ex.getMessage(), LocalDateTime.now());
		        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(error);
			    }
			    }
			    ```

Then your controllers stay clean:

```java
@GetMapping("/user/{id}")
public User getUser(@PathVariable Long id) {
    return userService.findById(id)  // throws UserNotFoundException if not found
    }
    ```

The key insight: `ResponseEntity` gives you precise HTTP control when you need it, but Spring's defaults are good enough for simple cases.




---



every aspect of the HTTP response, while still maintaining Spring's convention-over-configuration philosophy for the simple cases.

## The Core Concept: HTTP Response Control

Let's start with the most basic example to understand what `ResponseEntity` actually does. Consider this simple controller method:

```java
@GetMapping("/user/{id}")
public User getUser(@PathVariable Long id) {
    return userService.findById(id);
    }
    ```

This looks clean and simple. Spring does a lot of magic behind the scenes here. When you return a `User` object, Spring automatically:

1. Serializes the User object to JSON (using Jackson by default)
2. Sets the HTTP status code to 200 OK
3. Sets the Content-Type header to "application/json"
4. Wraps everything in a proper HTTP response

But there's a significant problem lurking here. What happens when `userService.findById(id)` returns null because the user doesn't exist? Spring will still return a 200 OK status with a null body. This is semantically incorrect - a 200 OK means "success, here's what you asked for," but we don't actually have what they asked for. The proper HTTP status code would be 404 Not Found.

This is where `ResponseEntity` comes in. It allows you to explicitly control the response:

```java
@GetMapping("/user/{id}")
public ResponseEntity<User> getUser(@PathVariable Long id) {
    User user = userService.findById(id);

    if (user == null) {
            return ResponseEntity.notFound().build();
	        }

    return ResponseEntity.ok(user);
    }
    ```

Now we're properly communicating with the client using HTTP semantics. If the user exists, we return 200 OK with the user data. If not, we return 404 Not Found with no body. The client can now programmatically handle these different scenarios appropriately.

## The Three Components of ResponseEntity

To truly understand `ResponseEntity`, you need to understand that every HTTP response consists of three parts, and `ResponseEntity` gives you control over all of them:

### 1. The Status Code

The status code is a three-digit number that tells the client what happened with their request. These aren't arbitrary - they're part of the HTTP specification and have specific meanings:

- **2xx Success**: The request was successful
  - 200 OK: Success, here's your data
    - 201 Created: Success, a new resource was created
      - 204 No Content: Success, but there's nothing to return

- **3xx Redirection**: The client needs to take additional action
  - 301 Moved Permanently: This resource is now at a different URL
    - 304 Not Modified: You already have the latest version (caching)

- **4xx Client Error**: The client did something wrong
  - 400 Bad Request: Your request data is malformed
    - 401 Unauthorized: You need to authenticate
      - 403 Forbidden: You're authenticated but don't have permission
        - 404 Not Found: This resource doesn't exist

- **5xx Server Error**: The server encountered a problem
  - 500 Internal Server Error: Something went wrong on our end
    - 503 Service Unavailable: The server is temporarily down

Choosing the correct status code is crucial for building a proper REST API. It allows clients to handle different scenarios programmatically. For example, a mobile app might retry on a 503 (temporary server issue) but not on a 404 (the resource simply doesn't exist).

Here's how you set status codes with `ResponseEntity`:

```java
// Using convenience methods (recommended)
return ResponseEntity.ok(data);              // 200 OK
return ResponseEntity.notFound().build();    // 404 Not Found
return ResponseEntity.noContent().build();   // 204 No Content

// Using the status() method for any status
return ResponseEntity.status(HttpStatus.CREATED).body(data);  // 201 Created
return ResponseEntity.status(418).body("I'm a teapot");       // Custom status code
```

### 2. The Headers

Headers are key-value pairs that provide metadata about the response. They're incredibly important but often overlooked. Headers can control caching, specify content types, provide additional information about resources, and much more.

Some common headers and why they matter:

**Content-Type**: Tells the client what format the data is in. Spring usually sets this automatically to `application/json`, but you might need to override it for file downloads or XML responses.

**Cache-Control**: Tells browsers and intermediate proxies whether and how long they can cache this response. This can dramatically improve performance by reducing unnecessary requests to your server.

**Location**: When you create a new resource (POST request), this header tells the client the URL where they can access the newly created resource. This is a REST best practice.

**ETag**: A version identifier for the resource. Clients can use this to check if they already have the latest version, avoiding unnecessary data transfer.

**Content-Disposition**: Controls how the browser handles the response - should it display it inline or trigger a download?

Here's how you work with headers:

```java
return ResponseEntity
    .ok()
        .header("X-Custom-Header", "my-value")
	    .header("X-Another-Header", "another-value")
	        .body(data);

// Or using HttpHeaders for more control
HttpHeaders headers = new HttpHeaders();
headers.setCacheControl(CacheControl.maxAge(1, TimeUnit.HOURS));
headers.setContentType(MediaType.APPLICATION_PDF);
return ResponseEntity.ok().headers(headers).body(data);
```

### 3. The Body

The body is the actual data you're sending back. This is what most developers focus on, but it's just one piece of the puzzle. The body can be:

- A single object (User, Product, etc.)
- A collection (List<User>, Set<Product>)
- Null (for responses like 204 No Content or 404 Not Found)
- Raw bytes (for file downloads)
- An error message or error object

The generic type `<T>` in `ResponseEntity<T>` specifies what type the body is:

```java
ResponseEntity<User>          // Body is a User object
ResponseEntity<List<User>>    // Body is a list of Users
ResponseEntity<Void>          // No body (null)
ResponseEntity<byte[]>        // Raw bytes
```

## Building ResponseEntity Objects

There are two main ways to create a `ResponseEntity`: using the builder pattern or using the constructor. Let's explore both and understand when to use each.

### The Builder Pattern (Recommended)

The builder pattern is more readable and expressive. It clearly shows what you're setting:

```java
return ResponseEntity
    .status(HttpStatus.CREATED)
        .header("X-Request-Id", requestId)
	    .header("X-Processing-Time", processingTime)
	        .body(createdUser);
		```

This reads almost like English: "Return a response entity with status CREATED, with these headers, and this body." The builder pattern also provides convenience methods for common scenarios:

```java
// These are shortcuts that set the appropriate status code
ResponseEntity.ok(data)                    // 200 OK with body
ResponseEntity.ok().build()                // 200 OK with no body
ResponseEntity.created(location).body(data) // 201 Created with Location header
ResponseEntity.accepted().body(data)        // 202 Accepted
ResponseEntity.noContent().build()          // 204 No Content
ResponseEntity.badRequest().body(error)     // 400 Bad Request
ResponseEntity.notFound().build()           // 404 Not Found
```

Notice that some of these use `.build()` and some use `.body()`. The `.build()` method is used when there's no response body - it finalizes the builder and creates the `ResponseEntity`. The `.body()` method sets the body and automatically calls `.build()` for you.

### The Constructor (When You Need It)

Sometimes you might need to use the constructor directly, especially when you're building the headers separately:

```java
HttpHeaders headers = new HttpHeaders();
headers.setContentType(MediaType.APPLICATION_JSON);
headers.setCacheControl(CacheControl.maxAge(Duration.ofHours(1)));

return new ResponseEntity<>(userData, headers, HttpStatus.OK);
```

This is less common but can be useful when you have complex header manipulation logic that you want to separate from the response creation.

## Real-World Patterns and Examples

Now let's look at how `ResponseEntity` is used in real applications, with detailed explanations of why each pattern exists and what problems it solves.

### Pattern 1: Handling Optional Resources

One of the most common patterns in REST APIs is fetching a resource that might not exist. Java's `Optional` combined with `ResponseEntity` creates an elegant solution:

```java
@GetMapping("/user/{id}")
public ResponseEntity<User> getUser(@PathVariable Long id) {
    return userService.findById(id)
            .map(ResponseEntity::ok)
	            .orElse(ResponseEntity.notFound().build());
		    }
		    ```

Let's break down what's happening here. The `userService.findById(id)` returns an `Optional<User>`. If the user exists, `map(ResponseEntity::ok)` transforms it into `Optional<ResponseEntity<User>>` containing a 200 OK response with the user. If the user doesn't exist, `orElse()` provides the fallback: a 404 Not Found response with no body.

This pattern is concise but powerful. It ensures you never accidentally return a null body with a 200 OK status. It properly uses HTTP semantics to communicate the result of the operation.

### Pattern 2: Creating Resources with Location Headers

When a client creates a new resource via a POST request, REST best practices dictate that you should:
1. Return a 201 Created status (not 200 OK)
2. Include a Location header pointing to the new resource
3. Optionally return the created resource in the body

Here's the complete pattern:

```java
@PostMapping("/users")
public ResponseEntity<User> createUser(@RequestBody User user) {
    // Save the user to the database
        User savedUser = userService.save(user);

    // Build the URI for the new resource
        // This constructs a URI like: http://localhost:8080/api/users/123
	    URI location = ServletUriComponentsBuilder
	            .fromCurrentRequest()           // Start with the current request URL
		            .path("/{id}")                  // Append /{id} to the path
			            .buildAndExpand(savedUser.getId())  // Replace {id} with actual ID
				            .toUri();                       // Convert to URI

    return ResponseEntity
            .created(location)              // 201 Created with Location header
	            .body(savedUser);               // Include the created user in the body
		    }
		    ```

Why is this important? The Location header tells the client exactly where they can access the newly created resource. This follows the HATEOAS principle (Hypermedia as the Engine of Application State) - the server provides the client with the information needed to interact with the API.

The client receives something like:

```
HTTP/1.1 201 Created
Location: http://localhost:8080/api/users/123
Content-Type: application/json

{
  "id": 123,
    "name": "John Doe",
      "email": "john@example.com"
      }
      ```

The client can now either use the returned object immediately or make a GET request to the Location URL to retrieve the resource later.

### Pattern 3: Successful Deletion with No Content

When you delete a resource, there's typically nothing to return. The operation either succeeded or failed. HTTP provides a perfect status code for this: 204 No Content. It means "I successfully did what you asked, but there's nothing to send back."

```java
@DeleteMapping("/user/{id}")
public ResponseEntity<Void> deleteUser(@PathVariable Long id) {
    if (!userService.exists(id)) {
            return ResponseEntity.notFound().build();
	        }

    userService.delete(id);
        return ResponseEntity.noContent().build();
	}
	```

Notice the generic type is `ResponseEntity<Void>`. This explicitly indicates there's no body. We first check if the user exists - if not, we return 404 Not Found (you can't delete something that doesn't exist). If the deletion succeeds, we return 204 No Content.

Some developers wonder: why not just return 200 OK? The semantic difference matters. 200 OK traditionally implies "here's the result of your request" - you expect a body. 204 No Content explicitly says "success, and there's intentionally no body to return." This clarity helps API consumers write better client code.

### Pattern 4: File Downloads with Proper Headers

Serving file downloads requires careful header management. You need to tell the browser the content type and whether to display the file inline or trigger a download:

```java
@GetMapping("/download/{fileId}")
public ResponseEntity<Resource> downloadFile(@PathVariable Long fileId) {
    // Load the file (this might be from disk, database, S3, etc.)
        Resource file = fileService.loadFile(fileId);

    if (file == null || !file.exists()) {
            return ResponseEntity.notFound().build();
	        }

    // Determine the content type
        String contentType = fileService.getContentType(fileId);

    return ResponseEntity.ok()
            // This header triggers a download with the specified filename
	            .header(HttpHeaders.CONTENT_DISPOSITION,
		                    "attachment; filename=\"" + file.getFilename() + "\"")
				            // Tell the browser what type of file this is
					            .contentType(MediaType.parseMediaType(contentType))
						            // Specify the file size (helps with progress bars)
							            .contentLength(file.contentLength())
								            .body(file);
									    }
									    ```

The `Content-Disposition` header is crucial here. With `attachment`, the browser downloads the file. If you use `inline` instead, the browser tries to display it (useful for PDFs or images). The `filename` parameter suggests what to name the downloaded file.

### Pattern 5: Caching with Cache-Control Headers

Proper caching can dramatically improve your API's performance by reducing unnecessary requests. The Cache-Control header tells browsers and intermediate proxies how to cache your response:

```java
@GetMapping("/product/{id}")
public ResponseEntity<Product> getProduct(@PathVariable Long id) {
    Product product = productService.findById(id);

    if (product == null) {
            return ResponseEntity.notFound().build();
	        }

    return ResponseEntity.ok()
            // Cache for 1 hour; after that, must revalidate with server
	            .cacheControl(CacheControl.maxAge(1, TimeUnit.HOURS)
		                .cachePrivate()     // Only browser can cache, not shared proxies
				            .mustRevalidate())  // Must check with server after max-age expires
					            .body(product);
						    }
						    ```

Let's understand what each directive means:

- `maxAge(1, TimeUnit.HOURS)`: The response is considered fresh for one hour. During this time, the browser won't even make a request to your server - it'll use the cached version.

- `cachePrivate()`: Only the end user's browser can cache this, not shared proxies. Use this for user-specific data.

- `mustRevalidate()`: After the max-age expires, the client must check with the server before using the cached copy.

For public, rarely-changing data, you might use:

```java
.cacheControl(CacheControl.maxAge(24, TimeUnit.HOURS).cachePublic())
```

This allows intermediate proxies (like CDNs) to cache the response, reducing load on your servers even further.

### Pattern 6: ETags for Conditional Requests

ETags (entity tags) are version identifiers for resources. They enable efficient caching and help prevent the "lost update" problem:

```java
@GetMapping("/document/{id}")
public ResponseEntity<Document> getDocument(
        @PathVariable Long id,
	        @RequestHeader(value = "If-None-Match", required = false) String ifNoneMatch) {

    Document doc = documentService.findById(id);

    if (doc == null) {
            return ResponseEntity.notFound().build();
	        }

    // Generate ETag from version or content hash
        String etag = "\"" + doc.getVersion() + "\"";

    // If client's ETag matches, resource hasn't changed
        if (etag.equals(ifNoneMatch)) {
	        return ResponseEntity
		            .status(HttpStatus.NOT_MODIFIED)
			                .eTag(etag)
					            .build();  // No body - client already has it
						        }

    // Resource has changed, send new version
        return ResponseEntity.ok()
	        .eTag(etag)
		        .body(doc);
			}
			```

Here's how this works in practice:

1. First request: Client requests the document. Server returns it with ETag header: `ETag: "42"` (version 42)
2. Client caches the document with its ETag
3. Second request: Client sends `If-None-Match: "42"` header
4. Server checks: is version still 42? Yes → returns 304 Not Modified with no body
5. Client uses cached version, saving bandwidth and processing time

For updates, ETags prevent the lost update problem:

```java
@PutMapping("/document/{id}")
public ResponseEntity<Document> updateDocument(
        @PathVariable Long id,
	        @RequestHeader(value = "If-Match", required = true) String ifMatch,
		        @RequestBody Document document) {

    Document existing = documentService.findById(id);

    if (existing == null) {
            return ResponseEntity.notFound().build();
	        }

    String currentETag = "\"" + existing.getVersion() + "\"";

    // Verify the client has the current version
        if (!currentETag.equals(ifMatch)) {
	        return ResponseEntity
		            .status(HttpStatus.PRECONDITION_FAILED)
			                .body(existing);  // Send the current version
					    }

    // Safe to update
        Document updated = documentService.update(id, document);
	    return ResponseEntity.ok()
	            .eTag("\"" + updated.getVersion() + "\"")
		            .body(updated);
			    }
			    ```

This prevents two users from overwriting each other's changes. If User A and User B both load version 42, then User A updates it to version 43, User B's update will fail with 412 Precondition Failed because they're trying to update version 42, which no longer exists.

## Complete CRUD Example with Explanations

Let's put it all together with a complete CRUD controller that follows REST best practices:

```java
@RestController
@RequestMapping("/api/products")
@RequiredArgsConstructor
public class ProductController {

    private final ProductService productService;

    /**
         * GET /api/products/{id}
	      * Retrieve a single product
	           *
		        * Returns:
			     * - 200 OK with product if found
			          * - 404 Not Found if product doesn't exist
				       * - Includes ETag for caching
				            * - Cache for 5 minutes
					         */
						     @GetMapping("/{id}")
						         public ResponseEntity<Product> getProduct(@PathVariable Long id) {
							         return productService.findById(id)
								             .map(product -> ResponseEntity.ok()
									                     .cacheControl(CacheControl.maxAge(5, TimeUnit.MINUTES))
											                     .eTag(String.valueOf(product.getVersion()))
													                     .body(product))
															                 .orElse(ResponseEntity.notFound().build());
																	     }

    /**
         * GET /api/products
	      * List all products with pagination
	           *
		        * Returns:
			     * - 200 OK with product list
			          * - Includes Link header for pagination
				       * - Cache for 1 minute
				            */
					        @GetMapping
						    public ResponseEntity<List<Product>> listProducts(
						                @RequestParam(defaultValue = "0") int page,
								            @RequestParam(defaultValue = "20") int size) {

        Page<Product> productPage = productService.findAll(page, size);

        // Build Link header for pagination (RFC 5988)
	        String linkHeader = buildPaginationLinks(page, size, productPage.getTotalPages());

        return ResponseEntity.ok()
	            .header("Link", linkHeader)
		                .header("X-Total-Count", String.valueOf(productPage.getTotalElements()))
				            .cacheControl(CacheControl.maxAge(1, TimeUnit.MINUTES).cachePublic())
					                .body(productPage.getContent());
							    }

    /**
         * POST /api/products
	      * Create a new product
	           *
		        * Returns:
			     * - 201 Created with Location header pointing to new resource
			          * - Body contains the created product with generated ID
				       * - 400 Bad Request if validation fails
				            */
					        @PostMapping
						    public ResponseEntity<Product> createProduct(
						                @Valid @RequestBody Product product) {

        // Save the product (generates ID, timestamps, etc.)
	        Product savedProduct = productService.save(product);

        // Build URI for the new resource
	        URI location = ServletUriComponentsBuilder
		            .fromCurrentRequest()
			                .path("/{id}")
					            .buildAndExpand(savedProduct.getId())
						                .toUri();

        return ResponseEntity
	            .created(location)
		                .body(savedProduct);
				    }

    /**
         * PUT /api/products/{id}
	      * Update an existing product
	           *
		        * Returns:
			     * - 200 OK with updated product
			          * - 404 Not Found if product doesn't exist
				       * - 400 Bad Request if validation fails
				            * - Includes new ETag
					         */
						     @PutMapping("/{id}")
						         public ResponseEntity<Product> updateProduct(
							             @PathVariable Long id,
								                 @Valid @RequestBody Product product) {

        if (!productService.exists(id)) {
	            return ResponseEntity.notFound().build();
		            }

        Product updated = productService.update(id, product);

        return ResponseEntity.ok()
	            .eTag(String.valueOf(updated.getVersion()))
		                .body(updated);
				    }

    /**
         * PATCH /api/products/{id}
	      * Partially update a product
	           *
		        * PATCH is for partial updates (update only specified fields)
			     * PUT is for complete replacement
			          *
				       * Returns:
				            * - 200 OK with updated product
					         * - 404 Not Found if product doesn't exist
						      */
						          @PatchMapping("/{id}")
							      public ResponseEntity<Product> partialUpdate(
							                  @PathVariable Long id,
									              @RequestBody Map<String, Object> updates) {

        return productService.findById(id)
	            .map(product -> {
		                    Product patched = productService.applyPartialUpdate(product, updates);
				                    return ResponseEntity.ok()
						                        .eTag(String.valueOf(patched.getVersion()))
									                    .body(patched);
											                })
													            .orElse(ResponseEntity.notFound().build());
														        }

    /**
         * DELETE /api/products/{id}
	      * Delete a product
	           *
		        * Returns:
			     * - 204 No Content if successfully deleted
			          * - 404 Not Found if product doesn't exist
				       * - No body in either case
				            */
					        @DeleteMapping("/{id}")
						    public ResponseEntity<Void> deleteProduct(@PathVariable Long id) {
						            if (!productService.exists(id)) {
							                return ResponseEntity.notFound().build();
									        }

        productService.delete(id);
	        return ResponseEntity.noContent().build();
		    }

    /**
         * Helper method to build RFC 5988 Link headers for pagination
	      */
	          private String buildPaginationLinks(int page, int size, int totalPages) {
		          StringBuilder links = new StringBuilder();

        // Link to first page
	        if (page > 0) {
		            links.append(String.format("</api/products?page=0&size=%d>; rel=\"first\", ", size));
			            }

        // Link to previous page
	        if (page > 0) {
		            links.append(String.format("</api/products?page=%d&size=%d>; rel=\"prev\", ",
			                    page - 1, size));
					            }

        // Link to next page
	        if (page < totalPages - 1) {
		            links.append(String.format("</api/products?page=%d&size=%d>; rel=\"next\", ",
			                    page + 1, size));
					            }

        // Link to last page
	        if (page < totalPages - 1) {
		            links.append(String.format("</api/products?page=%d&size=%d>; rel=\"last\"",
			                    totalPages - 1, size));
					            }

        return links.toString();
	    }
	    }
	    ```

This controller demonstrates several important concepts:

1. **Semantic HTTP**: Each method uses the correct HTTP verb and status codes
2. **RESTful design**: Resources are properly identified by URIs
3. **Caching strategies**: Different caching policies for different endpoints
4. **Pagination**: Proper pagination with Link headers following RFC 5988
5. **Versioning**: ETags for optimistic concurrency control
6. **No unnecessary data**: 204 for deletions, 404 when appropriate

## When NOT to Use ResponseEntity

It's important to understand that `ResponseEntity` adds complexity, and you shouldn't use it unless you need the control it provides. For simple cases where you just want to return data with 200 OK, skip it:

```java
// Don't do this - it's overkill
@GetMapping("/users")
public ResponseEntity<List<User>> getUsers() {
    return ResponseEntity.ok(userService.findAll());
    }

// Do this instead - cleaner and simpler
@GetMapping("/users")
public List<User> getUsers() {
    return userService.findAll();
    }
    ```

Spring automatically handles the serialization and sets the appropriate status code. You only need `ResponseEntity` when you're doing something beyond the defaults:

- Setting non-200 status codes
- Adding custom headers
- Conditional responses based on business logic
- Following specific REST conventions (like Location headers)

## Exception Handling Alternative

For many error cases, using `@ExceptionHandler` in a `@RestControllerAdvice` is cleaner than cluttering your controller methods with error-handling `ResponseEntity` objects:

```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(ResourceNotFoundException.class)
        public ResponseEntity<ErrorResponse> handleNotFound(ResourceNotFoundException ex) {
	        ErrorResponse error = new ErrorResponse(
		            HttpStatus.NOT_FOUND.value(),
			                ex.getMessage(),
					            LocalDateTime.now()
						            );
							            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(error);
								        }

    @ExceptionHandler(ValidationException.class)
        public ResponseEntity<ErrorResponse> handleValidation(ValidationException ex) {
	        ErrorResponse error = new ErrorResponse(
		            HttpStatus.BAD_REQUEST.value(),
			                ex.getMessage(),
					            LocalDateTime.now()
						            );
							            return ResponseEntity.badRequest().body(error);
								        }

    @ExceptionHandler(Exception.class)
        public ResponseEntity<ErrorResponse> handleGenericError(Exception ex) {
	        ErrorResponse error = new ErrorResponse(
		            HttpStatus.INTERNAL_SERVER_ERROR.value(),
			                "An unexpected error occurred",
					            LocalDateTime.now()
						            );
							            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
								        }
									}
									```

Now your controllers can throw exceptions, and the exception handler takes care of converting them to proper HTTP responses:

```java
@GetMapping("/user/{id}")
public User getUser(@PathVariable Long id) {
    return userService.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("User not found: " + id));
	    }
	    ```

This separation of concerns keeps your controllers focused on business logic while centralizing error handling.

## Conclusion

`ResponseEntity` is Spring's mechanism for giving you complete control over HTTP responses. It allows you to properly implement REST APIs by controlling status codes, headers, and response bodies. The key is knowing when to use it - reach for `ResponseEntity` when you need to do something beyond returning data with 200 OK, but keep it simple when you don't need the extra control.