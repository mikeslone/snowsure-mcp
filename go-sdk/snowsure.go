// Package snowsure is the official Go client for the SnowSure API
// (https://www.snowsure.ai) — live snow conditions, 14-day multi-model
// forecasts, powder rankings, and a grounded Answer Engine across 500+ ski
// resorts worldwide. Reads are free and need no authentication.
//
//	c := snowsure.New()
//	report, _ := c.SnowReport(ctx, nil)
//	resort, _ := c.Resort(ctx, "aspen-mountain")
//	ans, _ := c.Ask(ctx, "how much snow at Zermatt this week?", nil)
//
// See https://www.snowsure.ai/developers and the OpenAPI spec at
// https://www.snowsure.ai/openapi.json.
package snowsure

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strconv"
	"time"
)

// DefaultBaseURL is the SnowSure REST API root.
const DefaultBaseURL = "https://www.snowsure.ai/api/v1"

// Client is a SnowSure API client. Create one with New.
type Client struct {
	BaseURL    string
	APIKey     string // optional; only account/answer-engine tiers require it
	PartnerID  string // sent to the Answer Engine; "chatgpt" is keyless
	HTTPClient *http.Client
}

// Option configures a Client.
type Option func(*Client)

// WithAPIKey sets an X-API-Key sent on requests that require it.
func WithAPIKey(key string) Option { return func(c *Client) { c.APIKey = key } }

// WithBaseURL overrides the API root (e.g. for testing).
func WithBaseURL(base string) Option { return func(c *Client) { c.BaseURL = base } }

// WithHTTPClient supplies a custom *http.Client.
func WithHTTPClient(h *http.Client) Option { return func(c *Client) { c.HTTPClient = h } }

// WithPartnerID overrides the Answer Engine partner id (default "chatgpt").
func WithPartnerID(id string) Option { return func(c *Client) { c.PartnerID = id } }

// New returns a SnowSure client with sensible defaults.
func New(opts ...Option) *Client {
	c := &Client{
		BaseURL:    DefaultBaseURL,
		PartnerID:  "chatgpt",
		HTTPClient: &http.Client{Timeout: 30 * time.Second},
	}
	for _, o := range opts {
		o(c)
	}
	return c
}

// APIError is a non-2xx response from the SnowSure API.
type APIError struct {
	StatusCode int
	Message    string
}

func (e *APIError) Error() string {
	return fmt.Sprintf("snowsure: HTTP %d: %s", e.StatusCode, e.Message)
}

// envelope is the standard {meta, data} response wrapper.
type envelope struct {
	Meta json.RawMessage `json:"meta"`
	Data json.RawMessage `json:"data"`
	Err  string          `json:"error"`
}

func (c *Client) do(ctx context.Context, method, path string, query url.Values, body any) (json.RawMessage, error) {
	u := c.BaseURL + path
	if len(query) > 0 {
		u += "?" + query.Encode()
	}

	var reader io.Reader
	if body != nil {
		b, err := json.Marshal(body)
		if err != nil {
			return nil, err
		}
		reader = bytes.NewReader(b)
	}

	req, err := http.NewRequestWithContext(ctx, method, u, reader)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Accept", "application/json")
	req.Header.Set("User-Agent", "snowsure-go/0.1.0")
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	if c.APIKey != "" {
		req.Header.Set("X-API-Key", c.APIKey)
	}

	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	raw, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var env envelope
	_ = json.Unmarshal(raw, &env) // best-effort; errors may be bare too

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		msg := env.Err
		if msg == "" {
			msg = string(raw)
		}
		return nil, &APIError{StatusCode: resp.StatusCode, Message: msg}
	}
	if env.Data != nil {
		return env.Data, nil
	}
	return raw, nil
}

// ResortsOptions filters the resort list.
type ResortsOptions struct {
	Limit   int
	Offset  int
	Country string
	Sort    string
}

// Resorts returns all resorts with current conditions (GET /resorts).
// The result is the unwrapped data array as generic JSON.
func (c *Client) Resorts(ctx context.Context, opts *ResortsOptions) ([]map[string]any, error) {
	q := url.Values{}
	if opts != nil {
		if opts.Limit > 0 {
			q.Set("limit", strconv.Itoa(opts.Limit))
		}
		if opts.Offset > 0 {
			q.Set("offset", strconv.Itoa(opts.Offset))
		}
		if opts.Country != "" {
			q.Set("country", opts.Country)
		}
		if opts.Sort != "" {
			q.Set("sort", opts.Sort)
		}
	}
	data, err := c.do(ctx, http.MethodGet, "/resorts", q, nil)
	if err != nil {
		return nil, err
	}
	var out []map[string]any
	if err := json.Unmarshal(data, &out); err != nil {
		return nil, err
	}
	return out, nil
}

// Resort returns one resort by slug, e.g. "niseko-hanazono-resort"
// (GET /resorts/{slug}).
func (c *Client) Resort(ctx context.Context, slug string) (map[string]any, error) {
	if slug == "" {
		return nil, fmt.Errorf("snowsure: slug is required")
	}
	data, err := c.do(ctx, http.MethodGet, "/resorts/"+url.PathEscape(slug), nil, nil)
	if err != nil {
		return nil, err
	}
	var out map[string]any
	if err := json.Unmarshal(data, &out); err != nil {
		return nil, err
	}
	return out, nil
}

// SnowReportOptions filters the ranked snow report.
type SnowReportOptions struct {
	Limit int
}

// SnowReport returns resorts ranked by current conditions (GET /snow-report).
func (c *Client) SnowReport(ctx context.Context, opts *SnowReportOptions) (map[string]any, error) {
	q := url.Values{}
	if opts != nil && opts.Limit > 0 {
		q.Set("limit", strconv.Itoa(opts.Limit))
	}
	data, err := c.do(ctx, http.MethodGet, "/snow-report", q, nil)
	if err != nil {
		return nil, err
	}
	var out map[string]any
	if err := json.Unmarshal(data, &out); err != nil {
		return nil, err
	}
	return out, nil
}

// AskOptions scopes an Answer Engine query.
type AskOptions struct {
	ResortSlug string
	Locale     string // en | es | fr | de | it | ja
	Format     string // "markdown" (default) | "json"
}

// Ask sends a natural-language question to the SnowSure Answer Engine
// (POST /ask). data["answer"] holds the grounded answer text.
func (c *Client) Ask(ctx context.Context, question string, opts *AskOptions) (map[string]any, error) {
	if question == "" {
		return nil, fmt.Errorf("snowsure: question is required")
	}
	body := map[string]any{
		"question":  question,
		"partnerId": c.PartnerID,
		"format":    "markdown",
	}
	if opts != nil {
		if opts.Format != "" {
			body["format"] = opts.Format
		}
		if opts.ResortSlug != "" {
			body["resortSlug"] = opts.ResortSlug
		}
		if opts.Locale != "" {
			body["locale"] = opts.Locale
		}
	}
	data, err := c.do(ctx, http.MethodPost, "/ask", nil, body)
	if err != nil {
		return nil, err
	}
	var out map[string]any
	if err := json.Unmarshal(data, &out); err != nil {
		return nil, err
	}
	return out, nil
}
