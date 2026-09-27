# Example business configs

**Recommended: RizzDial for calls + Beam for texts.** Use these niche configs as reviewed greeting, hours, FAQ and transfer-rule content for a managed agent. Follow the [RizzDial + Beam guide](../docs/RIZZDIAL_AND_BEAM.md) for MCP verification and the content mapping. The offline and DIY Twilio commands below still work.

Ready-made `business.yaml` files for common niches. Every file here is a
fictional business (555-01xx phone numbers, no real addresses) so you can
try the offline demo immediately, then copy the closest one as your
starting point.

This starter only handles inbound calls, so there is no lead list or CSV
format here. If you need to work from a call list, see the
`ai-cold-calling-agent` starter instead.

| Niche | File | Run it |
|---|---|---|
| Med spa / aesthetics | [niches/med_spa.yaml](niches/med_spa.yaml) | `python -m receptionist.simulate --config examples/niches/med_spa.yaml` |
| Home services (HVAC, plumbing, electrical) | [niches/home_services.yaml](niches/home_services.yaml) | `python -m receptionist.simulate --config examples/niches/home_services.yaml` |
| Marketing agency | [niches/marketing_agency.yaml](niches/marketing_agency.yaml) | `python -m receptionist.simulate --config examples/niches/marketing_agency.yaml` |
| Real estate brokerage | [niches/real_estate.yaml](niches/real_estate.yaml) | `python -m receptionist.simulate --config examples/niches/real_estate.yaml` |
| Independent insurance agency | [niches/insurance.yaml](niches/insurance.yaml) | `python -m receptionist.simulate --config examples/niches/insurance.yaml` |

To use one for real calls, copy it to the repo root as `business.yaml`,
edit the business name, hours, FAQs, and department phone numbers, then
follow the "Connect a real phone number" steps in the main
[README](../README.md):

```bash
cp examples/niches/med_spa.yaml business.yaml
```

Every greeting in these files discloses that the caller is talking to an
AI receptionist. Keep that disclosure, and your own local consent and
opt-out rules, when you edit these for a real business. Every file here
validates against the same `business.yaml` schema and is covered by
`tests/test_examples.py`, so a config that loads in the offline demo will
also load in the live server.
