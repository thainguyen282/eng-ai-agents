(define (domain provider-routing)
    (:requirements :strips :typing)
    (:types
        provider
        model
    )
    (:predicates
        (routes_to_provider ?model - model ?provider - provider)
        (prioritize_providers ?provider - provider)
        (load_balance_price)
        (load_balance_throughput)
        (complete_partial_response)
        (automatically_try_models)
        (normalize_schema)
        (send_completion_request ?model - model)
        (send_chat_completion_request ?model - model)
    )
    (:action route-request
        :parameters (?model - model ?provider - provider)
        :precondition (and
            (routes_to_provider ?model ?provider)
        )
        :effect (and
            (prioritize_providers ?provider)
        )
    )
    (:action prioritize-providers
        :parameters (?provider - provider)
        :effect (and
            (prioritize_providers ?provider)
        )
    )
    (:action load-balance-price
        :effect (and
            (load_balance_price)
        )
    )
    (:action load-balance-throughput
        :effect (and
            (load_balance_throughput)
        )
    )
    (:action complete-partial-response
        :effect (and
            (complete_partial_response)
        )
    )
    (:action auto-router
        :parameters (?model - model)
        :effect (and
            (automatically_try_models)
        )
    )
    (:action normalize-schema
        :effect (and
            (normalize_schema)
        )
    )
    (:action send-completion-request
        :parameters (?model - model)
        :effect (and
            (send_completion_request ?model)
        )
    )
    (:action send-chat-completion-request
        :parameters (?model - model)
        :effect (and
            (send_chat_completion_request ?model)
        )
    )
)
