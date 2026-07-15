package snowsure

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestResort(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/resorts/aspen-mountain" {
			t.Errorf("unexpected path %s", r.URL.Path)
		}
		_ = json.NewEncoder(w).Encode(map[string]any{
			"meta": map[string]any{"source": "test"},
			"data": map[string]any{"name": "Aspen Mountain", "slug": "aspen-mountain"},
		})
	}))
	defer srv.Close()

	c := New(WithBaseURL(srv.URL))
	got, err := c.Resort(context.Background(), "aspen-mountain")
	if err != nil {
		t.Fatal(err)
	}
	if got["slug"] != "aspen-mountain" {
		t.Errorf("got %v", got)
	}
}

func TestAskRequiresQuestion(t *testing.T) {
	c := New()
	if _, err := c.Ask(context.Background(), "", nil); err == nil {
		t.Error("expected error for empty question")
	}
}

func TestAPIError(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(404)
		_ = json.NewEncoder(w).Encode(map[string]any{"error": "Resort not found"})
	}))
	defer srv.Close()

	c := New(WithBaseURL(srv.URL))
	_, err := c.Resort(context.Background(), "nope")
	apiErr, ok := err.(*APIError)
	if !ok {
		t.Fatalf("expected *APIError, got %T", err)
	}
	if apiErr.StatusCode != 404 || apiErr.Message != "Resort not found" {
		t.Errorf("got %+v", apiErr)
	}
}
