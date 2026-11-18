# Review legacy observer permissions

Install only this host-side reviewer using any registered language and platform with `-- --component policy-review`. A C or C++ migration installation also includes it. Set `SDK` to the installation directory printed by the installer.

Export the legacy policy argument vector as a UTF-8 JSON array. Include full ROS1 or ROS2 global, single and group grant, set, enable, disable, create and membership options in their original order. Run the installed reviewer before rewriting a deployment permission recommendation.

```sh
python3 "$SDK/tools/migration/legacy_permissions.py" legacy-grants.json
```

Exit 2 identifies a policy that requires manual migration. The output names the observer, source, backend and target for each pair. A legacy service observation checks both the observation grant and the distinct service-call grant. It can require a bounded native wait. An event observer is tied to its own source capability and its permitted events. Preserve these relationships when deciding what to authorize. ROSv2 endpoint readiness, graph visibility and an event stream each prove different things. Using the same alias in two independent environments establishes no relationship.

Exit 0 reports that no paired observer declaration occurred among the recognized arguments. Exit 3 refuses malformed input or an unsupported option. The tool emits no grants, reads no credentials and starts no VM. Its report covers paired authority only. Separately review event kinds, budgets, rates, type identities and transport configuration before applying any new policy.
