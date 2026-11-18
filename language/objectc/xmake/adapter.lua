function describe()
    return {id = "objectc", program = "wrobjc", family = "c", extensions = {".m", ".o", ".a"}}
end

function validate(target, req)
    assert(req.core == "3.0" and not req.threads, "Objective-C requires Core 3.0 and a single guest thread")
end
