"""
SOFIPOs Monitor Tentacle for Project Nikkei.
Checks current investment yield rates for Mexican SOFIPOs and calculates projected returns.
"""
from typing import Dict, Any, Literal
from pydantic import BaseModel, Field

from tentacles.base import Tentacle
from tentacles.suckers.web_search import GeminiSearchSucker

class SofipoArgs(BaseModel):
    action: Literal["rates", "calculate"] = Field(..., description="The action to perform: 'rates' or 'calculate'")
    amount: float = Field(default=10000.0, description="The principal investment amount (used for 'calculate')")
    months: int = Field(default=12, description="The investment duration in months (used for 'calculate')")


class SofipoMonitorTentacle(Tentacle):
    """
    Financial monitor for Mexican SOFIPOs. Provides current yield rates
    and calculates projected simple interest returns.
    """
    tool_name = "sofipos_monitor"
    tool_description = "Checks current investment yield rates for Mexican SOFIPOs and calculates projected returns."
    args_schema = SofipoArgs
    requires_approval = False  # Read-only data operation

    def __init__(self):
        super().__init__(sucker=GeminiSearchSucker())

    def _execute(self, action: str, amount: float = 10000.0, months: int = 12) -> Dict[str, Any]:
        print(f"[SofipoMonitor Tentacle] Action: {action} | Amount: ${amount:,.2f} | Months: {months}")

        # Live extraction of current rates
        prompt = (
            "Search the web for the current 2026 annual yield rates (GAT Nominal) "
            "for Mexican SOFIPOs (Nu, Klar, Finsus, Fondeadora, Stori). "
            "Return ONLY a valid JSON dictionary mapping the SOFIPO name to its float percentage rate."
        )
        current_rates = self.sucker.extract(prompt)
        
        if "error" in current_rates:
            return {"status": "error", "message": "Failed to extract live SOFIPO rates from web.", "data": current_rates}

        if action == "rates":
            # Return current rates sorted by highest yield
            sorted_rates = dict(sorted(current_rates.items(), key=lambda item: item[1] if isinstance(item[1], (int, float)) else 0, reverse=True))
            return {
                "status": "success",
                "data": sorted_rates,
                "message": "Current live annual SOFIPO yield rates"
            }

        elif action == "calculate":
            results = []
            for name, rate in current_rates.items():
                print(name)
                # Simple interest formula: P * r * t (where t is in years)
                time_in_years = months / 12.0
                profit = amount * (rate / 100.0) * time_in_years
                total_return = amount + profit
                
                results.append({
                    "sofipo": name,
                    "annual_rate": f"{rate}%",
                    "investment_amount": round(amount, 2),
                    "duration_months": months,
                    "projected_profit": round(profit, 2),
                    "total_return": round(total_return, 2)
                })

            # Sort by total return, descending
            results.sort(key=lambda x: x["total_return"], reverse=True)

            return {
                "status": "success",
                "data": results,
                "message": f"Projected returns for ${amount:,.2f} invested over {months} months."
            }

        else:
            return {
                "status": "error",
                "message": f"Invalid action '{action}'. Needs to be 'rates' or 'calculate'."
            }
