## Décoration et référencement des vues

Une vue décoré avec hapic ressemble à ça:

``` python
    @hapic.with_api_doc()
    @hapic.handle_exception(ZeroDivisionError, http_code=HTTPStatus.BAD_REQUEST)
    @hapic.input_path(HelloPathSchema())
    @hapic.input_query(HelloQuerySchema())
    @hapic.output_body(HelloResponseSchema())
    def hello(self, name: str, hapic_data: HapicData):
        pass
```

Lors de la première lecture par python, les méthodes hapic sont éxécutés:

```
 |  @hapic.with_api_doc()
 |  @hapic.handle_exception(ZeroDivisionError, http_code=HTTPStatus.BAD_REQUEST)
 |  @hapic.input_path(HelloPathSchema())
 |  @hapic.input_query(HelloQuerySchema())
 |  @hapic.output_body(HelloResponseSchema())
 V  def hello(self, name: str, hapic_data: HapicData):
```

Le décorateur prend comme valeur le retour de chaque méthodes.

Par exemple, avec `@hapic.with_api_doc()` c'est la fonction `decorator`
qui se trouve dans `hapic.hapic.Hapic#with_api_doc`. Avec `hapic.output_body` c'est
la fonction `decorator` qui se trouve dans `hapic.hapic.Hapic#output_body`. 

Ensuite, une fois arrivé à la méthode `hello`, python commence à remonter la file
de décorateurs en donnant à chaque décorateur "la fonction de dessous". Puis remplacera
"la fonction du dessous" avec le retour de ce décorateur:

```
 ^  @hapic.with_api_doc()
 |  @hapic.handle_exception(ZeroDivisionError, http_code=HTTPStatus.BAD_REQUEST)
 |  @hapic.input_path(HelloPathSchema())
 |  @hapic.input_query(HelloQuerySchema())
 |  @hapic.output_body(HelloResponseSchema())
 |  def hello(self, name: str, hapic_data: HapicData):
```

Par exemple, le décorateur à la ligne `@hapic.output_body(HelloResponseSchema())`
qui pour rappel est `hapic.hapic.Hapic#output_body.decorator` reçoit en paramètre la
fonction `hello`:

``` python
        def decorator(func):
            self._buffer.output_body = OutputBodyDescription(decoration)
            return decoration.get_wrapper(func)
```

Le retour de cette fonction remplacera la méthode `hello`. Au passage, la fonction
`decorator` à éxecuter la ligne 
`self._buffer.output_body = OutputBodyDescription(decoration)`. Ce qui à pour effet
d'alimenter l'objet buffer (`hapic.buffer.DecorationBuffer`) contenu dans l'instance
`hapic` (`hapic.hapic.Hapic`).

Lorsque l'on arrive au décorateur de la ligne `@hapic.with_api_doc()` (pour rappel
`hapic.hapic.Hapic#with_api_doc.decorator`), le décorateur éxecute le code suivant:

``` python
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            token = uuid.uuid4().hex
            setattr(wrapper, DECORATION_ATTRIBUTE_NAME, token)
            setattr(func, DECORATION_ATTRIBUTE_NAME, token)

            description = self._buffer.get_description()
            description.tags = tags

            reference = ControllerReference(
                wrapper=wrapper,
                wrapped=func,
                token=token,
            )
            decorated_controller = DecoratedController(
                reference=reference,
                description=description,
                name=func.__name__,
            )
            self._buffer.clear()
            self._controllers.append(decorated_controller)
            return wrapper
```

Ce que ça fait (en plus de retourner une fonction pour remplacer la 
"fonction du dessous)": Ca place des token sur la méthode décoré et sur le wrapper (
 pour retrouver la vue lors de la génération de la doc). Ca construit un objet
 `hapic.decorator.DecoratedController` qui est la représentation de la vue et qui 
 contient tout ce qu'on y a attaché (les schémas, les erreur attrapés, etc).

Avec ce système on à la liste de toute les vues et pour chaque vues les schémas, les
 erreur attrapés, etc.
 

## Éxécution d'un vue

Lorsque le framework web éxécute une vue, elle éxecute en premier lieu un wrapper. Si on 
regarde par exemple le wrapper mis en place par la ligne
 `@hapic.output_body(HelloResponseSchema())`: Rendez vous sur le code de 
 `hapic.hapic.Hapic#output_body`. On constate que le wrapper est fabriqué avec la
 méthode `hapic.decorator.OutputBodyControllerWrapper#get_wrapper`. Tous les décorateurs
 hapic sont basés sur ce principe: on fabrique le wrapper avec un objet enfant de la
 classe `hapic.decorator.ControllerWrapper`. le wrapper en question est:
 
``` python
        def wrapper(*args, **kwargs) -> typing.Any:
            # Note: Design of before_wrapped_func can be to update kwargs
            # by reference here
            replacement_response = self.before_wrapped_func(args, kwargs)
            if replacement_response is not None:
                return replacement_response

            response = self._execute_wrapped_function(func, args, kwargs)
            new_response = self.after_wrapped_function(response)
            return new_response
```

On fait donc systématiquement:

 1. `replacement_response = self.before_wrapped_func(args, kwargs)`: Executé avant la vue
   réelle: Dans le cas des `@hapic.input_xxx` on contrôle les entrées, voir
   `hapic.decorator.InputControllerWrapper#before_wrapped_func`. Si cette méthode
   retourne quelque chose, on bypass même la vue réelle (par exemple si on constate
   une erreur dans les entrées, la méthode retourne une vue contenant l'erreur)
 2. `response = self._execute_wrapped_function(func, args, kwargs)` On éxécute la vue
   réelle.
 3. `new_response = self.after_wrapped_function(response)`: Éxécute après la vue réelle:
   Dans le cas des `@hapic.output_xxx` on contrôle la sortie, voir
   `hapic.decorator.OutputControllerWrapper#after_wrapped_function`. C'est le retour de
   cette méthode qui sera le retour envoyé au framework.

## Génération de la doc OpenAPI

Il faut aller voir `hapic.doc.DocGenerator`. Ce que l'on peut dire c'est qu'en gros il
se base sur la liste de `hapic.decorator.DecoratedController` qui à été alimenté par
la fonction `hapic.hapic.Hapic#with_api_doc.decorator`.
