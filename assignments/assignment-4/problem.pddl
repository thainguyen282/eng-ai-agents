(define (problem provider-routing-1)
    (:domain provider-routing)
    (:objects
        model1 - model
        model2 - model
        provider1 - provider
        provider2 - provider
    )
    (:init
        (routes_to_provider model1 provider1)
        (routes_to_provider model2 provider2)
    )
    (:goal
        (and 
            (prioritize_providers provider1)
            (load_balance_price)
            (automatically_try_models)
        )
    )
)
